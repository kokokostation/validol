from io import StringIO

import pandas as pd
import requests
from validol.model.store.resource import Resource
from validol.model.utils import parse_isoformat_date


class Monetary(Resource):
    CSV_NAMES = {
        'DATE': 'Date',
        'BOGMBASEW': 'MBase'}
    SCHEMA = [("MBase", "INTEGER")]
    INDEPENDENT = True

    def __init__(self, model_launcher):
        Resource.__init__(self, model_launcher.main_dbh, "Monetary", Monetary.SCHEMA)

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

        return df.rename(index=str, columns=Monetary.CSV_NAMES)

    def fill(self, first, last):
        df = self.initial_fill()
        return df[(first < df["Date"]) & (df["Date"] <= last)]
