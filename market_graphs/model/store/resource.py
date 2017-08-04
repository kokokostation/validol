from datetime import date

import pandas as pd
from market_graphs.model.utils import date_to_timestamp, to_timestamp


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

    def read_df(self):
        return pd.read_sql('SELECT * FROM "{table}"'.format(table=self.table), self.dbh)


class Resource(Table):
    def __init__(self, dbh, table, schema):
        Table.__init__(self, dbh, table,
                       [("Date", "INTEGER PRIMARY KEY ON CONFLICT IGNORE")] + schema)

    def update(self):
        first, last = self.range()
        if last:
            self.write_df(self.fill(last, date.today()))
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
            return map(date.fromtimestamp, item)
        else:
            return item

    def read_dates(self, begin=None, end=date.today()):
        query = '''
            SELECT 
                * 
            FROM 
                "{table}"'''.format(table=self.table)
        params = None

        if begin:
            query += '''
            WHERE
                Date >= ? AND
                Date <= ?'''

            params = to_timestamp(begin), to_timestamp(end)

        df = pd.read_sql(query, self.dbh, params=params)

        return df

    def write_df(self, df):
        if not df.empty:
            df = date_to_timestamp(df)
            Table.write_df(self, df)

    @staticmethod
    def get_atoms(schema):
        return [atom[0] for atom in schema]