import datetime as dt
import pandas as pd
import numpy as np

from validol.model.utils import date_to_timestamp, to_timestamp


class Table:
    def __init__(self, dbh, table, schema, modifier=""):
        self.schema = [(name, data_type) for name, data_type in schema]
        self.table = table
        self.dbh = dbh

        self.__create_table(modifier)

    def __create_table(self, modifier):
        columns = [" ".join(['"{}"'.format(name), data_type]) for name, data_type in self.schema]

        if modifier:
            modifier = ", " + modifier

        self.dbh.cursor().execute(
            'CREATE TABLE IF NOT EXISTS "{table}" ({columns}{modifier})'.format(
                table=self.table,
                columns=",".join(columns),
                modifier=modifier))

    def read_all(self, query):
        return self.dbh.cursor().execute(query).fetch_all()

    def write(self, values):
        self.dbh.cursor().executemany('''
            INSERT INTO
                {table}
            VALUES
                ({values_num})
        '''.format(table=self.table, values_num=",".join('?' * len(self.schema))), values)

    def write_df(self, df):
        df.to_sql(self.table, self.dbh, if_exists='append', index=False)

    def read_df(self, query=None, **kwargs):
        if query is None:
            query = 'SELECT * FROM "{table}"'
        return pd.read_sql(query.format(table=self.table), self.dbh, **kwargs)

    def drop(self):
        self.dbh.cursor().execute('''
            DROP TABLE IF EXISTS
                "{table}"
        '''.format(table=self.table))


class Resource(Table):
    def __init__(self, dbh, table, schema, modifier="PRIMARY KEY (Date) ON CONFLICT IGNORE"):
        Table.__init__(self, dbh, table,
                       [("Date", "INTEGER")] + schema, modifier)

    def update(self):
        first, last = self.range()
        if last:
            if last != dt.date.today():
                self.write_df(self.fill(last + dt.timedelta(days=1), dt.date.today()))
        else:
            self.write_df(self.initial_fill())

    def initial_fill(self):
        raise NotImplementedError

    def fill(self, first, last):
        raise NotImplementedError

    def range(self):
        c = self.dbh.cursor()
        c.execute('''
        SELECT
            MIN(Date),
            MAX(Date)
        FROM
            "{table}"'''.format(table=self.table))

        item = c.fetchone()

        if item != (None,) * 2:
            return map(dt.date.fromtimestamp, item)
        else:
            return item

    def empty(self):
        return pd.DataFrame(columns=[name for name, _ in self.schema],
                            dtype=np.float64)

    def read_dates_dt(self, *args):
        return self.read_dates_ts(*map(to_timestamp, args))

    def read_dates_ts(self, begin=None, end=None):
        query = '''
            SELECT 
                * 
            FROM 
                "{table}"'''.format(table=self.table)

        cp = list(zip(*[(clause, int(param))
                        for clause, param in (('Date >= ?', begin), ('Date <= ?', end))
                        if param is not None]))

        if cp:
            clauses, params = cp

            query += 'WHERE {}'.format(' AND '.join(clauses))
        else:
            params = None

        return self.read_df(query, params=params)

    def read_df(self, query=None, index_on=True, **kwargs):
        if index_on:
            kwargs['index_col'] = 'Date'

        df = super().read_df(query, **kwargs)

        if index_on:
            df.sort_index(inplace=True)

        return df

    def write_df(self, df):
        if not df.empty:
            df = date_to_timestamp(df)
            Table.write_df(self, df)

    @staticmethod
    def get_atoms(schema):
        return [atom[0] for atom in schema]