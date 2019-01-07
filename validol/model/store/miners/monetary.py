from io import StringIO

import pandas as pd
import numpy as np
import requests

from functools import partial

from validol.model.store.resource import ResourceUpdater
from validol.model.utils.utils import parse_isoformat_date
from validol.model.store.resource import CompositeUpdater


class MonetaryType(ResourceUpdater):
    INDEPENDENT = True

    def __init__(self, model_launcher, config_key):
        self._config = Monetary.CONFIG[config_key]

        ResourceUpdater.__init__(self, model_launcher,
                                 model_launcher.main_dbh,
                                 'Monetary_{}'.format(config_key),
                                 self._config['schema'])

    def initial_fill(self):
        session = requests.Session()

        response = session.get(
            url='https://fred.stlouisfed.org/graph/fredgraph.csv',
            params={
                'id': self._config['id'],
            },
            headers={
                'Host': "fred.stlouisfed.org",
                'User-Agent': 'Mozilla/5.0'
            }
        )

        df = pd.read_csv(StringIO(response.text))
        df = df.replace('.', np.nan).dropna()
        df = df.rename(index=str, columns=self._config['rename'])
        df.Date = df.apply(lambda row: parse_isoformat_date(row['Date']), axis=1)

        return df

    def fill(self, first, last):
        df = self.initial_fill()
        return df[(first <= df.Date) & (df.Date <= last)]


class Monetary(CompositeUpdater):
    CONFIG = {
        'MBase': {
            'rename': {
                'DATE': 'Date',
                'BOGMBASEW': 'MBase'
            },
            'schema': [
                ('MBase', 'INTEGER')
            ],
            'id': 'BOGMBASEW'
        },
        'TDebt': {
            'rename': {
                'DATE': 'Date',
                'ASTDSL': 'TDebt'
            },
            'schema': [
                ('TDebt', 'INTEGER')
            ],
            'id': 'ASTDSL'
        }
    }

    def __init__(self, model_launcher):
        clss = [partial(MonetaryType, config_key=config_key) for config_key in self.CONFIG]

        CompositeUpdater.__init__(self, model_launcher, 'Monetary', clss)
