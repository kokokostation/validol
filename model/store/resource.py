from model.utils import to_timestamp
from datetime import date
import pandas as pd


class Table:
    def __init__(self, dbh, table, schema):
        self.schema = schema
        self.table = table
        self.dbh = dbh

        self.__create_table()

    def __create_table(self):
        columns = [" ".join([name, data_type]) for name, data_type in self.schema]

        self.dbh.cursor().execute(
            "CREATE TABLE IF NOT EXISTS {table} ({columns})".format(
                table=self.table,
                columns=",".join(columns)))

    def write(self, df):
        if not df.empty:
            df.Date = df.apply(lambda row: to_timestamp(row['Date']), axis=1)
            df.to_sql(self.table, self.dbh, if_exists='append', index=False)


class Resource(Table):
    def __init__(self, dbh, table, schema):
        Table.__init__(self, dbh, table, [("Date", "INTEGER PRIMARY KEY")] + schema)

    def update(self):
        first, last = self.range()
        if last:
            self.write(self.fill(last, date.today()))
        else:
            self.write(self.initial_fill())

    def initial_fill(self):
        raise NotImplementedError

    def fill(self, first, last):
        raise NotImplementedError

    def range(self):
        c = self.dbh.cursor()
        c.execute("""
        SELECT
            MIN(Date),
            MAX(Date)
        FROM
            {table}""".format(table=self.table))

        item = c.fetchone()

        if item != (None,) * 2:
            return map(date.fromtimestamp, item)
        else:
            return item

    def read(self, columns, begin, end=date.today()):
        columns += ['Date']

        c = self.dbh.cursor()
        c.execute("""
            SELECT 
                {columns} 
            FROM 
                {table}
            WHERE
                Date >= ? AND
                Date <= ?""".format(columns=",".join(columns), table=self.table),
            (
                to_timestamp(begin),
                to_timestamp(end)
            )
        )

        df = pd.DataFrame(c.fetchall(), columns=columns)
        if not df.empty:
            df.Date = df.apply(lambda row: date.fromtimestamp(row['Date']), axis=1)

        return df

    def get_atoms(self):
        return [atom[0] for atom in self.schema]

    def get_dates(self, requested_dates):
        pass