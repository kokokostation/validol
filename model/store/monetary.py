from model.store.resource import Resource
from io import StringIO
import pandas as pd
import requests
from model.utils import parse_isoformat_date, take_closest
from datetime import timedelta


class Monetary(Resource):
    def __init__(self, dbh):
        Resource.__init__(self, dbh, "Monetary", [("MBase", "INTEGER")])

    def initial_fill(self):
        session = requests.Session()

        response = session.get(
            url='https://fred.stlouisfed.org/graph/fredgraph.csv',
            params={
                'id': 'BOGMBASEW',
            },
            headers={
                'Host': "fred.stlouisfed.org",
                'User-Agent': 'Mozilla/5.0'
            }
        )

        df = pd.read_csv(StringIO(response.text))
        df.DATE = df.apply(lambda row: parse_isoformat_date(row['DATE']), axis=1)

        return df.rename(index=str, columns={'DATE': 'Date', 'BOGMBASEW': 'MBase'})

    def fill(self, first, last):
        df = self.initial_fill()
        return df[first <= df.Date <= last]

    def get_dates(self, requested_dates):
        df = self.read(['MBase'],
                       requested_dates[0] - timedelta(days=7),
                       requested_dates[-1] + timedelta(days=7))

        result = []
        for date in requested_dates:
            closest = take_closest(df.Date.tolist(), date)
            if abs(df.Date[closest].toordinal() - date.toordinal()) <= 7:
                result.append(df.MBase[closest])
            else:
                result.append(None)

        return result
