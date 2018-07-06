import datetime as dt
import pandas as pd
from requests import Request
from io import StringIO
from requests_cache import CachedSession

from validol.model.store.resource import Updatable, Platforms
from validol.model.utils.utils import concat
from validol.model.store.miners.weekly_reports.utils import active_iterator
from validol.model.store.utils import reduce_ranges
from validol.model.mine.utils import remove_from_cache
from validol.model.store.miners.weekly_reports.active import WeeklyActives, Active


class MoexUpdatable(Updatable):
    def __init__(self, model_launcher, flavor):
        self.model_launcher = model_launcher
        self.session = CachedSession()

    def download_date(self, date):
        request = Request(
            method='GET',
            url='https://www.moex.com/ru/derivatives/open-positions-csv.aspx',
            params={
                'd': dt.datetime(date.year, date.month, date.day).strftime("%Y%m%d")
            },
            headers={'User-Agent': 'Mozilla/5.0'}
        )

        request = self.session.prepare_request(request)
        response = self.session.send(request)

        df = pd.read_csv(StringIO(response.text), parse_dates=['moment'])

        if df.empty:
            remove_from_cache(self.session, request)

            return pd.DataFrame()

        df = df.rename(columns={'moment': 'Date', 'isin': 'code'})

        df.name = df.apply(lambda row: '{} ({})'.format(row['name'],
                                                        MOEX['ct_mapping'][row['contract_type']]), axis=1)
        df.iz_fiz.fillna(0, inplace=True)

        keys = ('Date', 'name')

        groups = df.groupby(keys)

        df = pd.DataFrame([{**{'{}{}'.format(MOEX['phys_mapping'][row['iz_fiz']], value): row[key]
                               for i, row in content.iterrows()
                               for key, value in MOEX['csv_mapping'].items()},
                            **dict(zip(keys, group))} for
                           group, content in groups])

        return df

    def initial_fill(self):
        return self.fill(MOEX['first_date'], dt.date.today())

    def fill(self, first, last):
        return concat([self.download_date(date) for date in pd.date_range(first, last)])

    def range(self):
        return reduce_ranges([active.range() for active in
                              active_iterator(MOEX, self.model_launcher)])

    def write_update(self, data):
        if not data.empty:
            Platforms(self.model_launcher, MOEX['name']).write_single(MOEX['platform_code'],
                                                                      'Moscow exchange')

            actives_table = WeeklyActives(self.model_launcher, MOEX['name'])

            groups = data.groupby('name')

            actives_table.write_df(pd.DataFrame([(MOEX['platform_code'], active)
                                                 for active in groups.groups.keys()],
                                                columns=("PlatformCode", "ActiveName")))

            for group, content in groups:
                Active(self.model_launcher, MOEX, MOEX['platform_code'],
                       group, content.drop('name', axis=1)).update()


MOEX = {
    'name': 'moex',
    'platform_code': 'MOEX',
    'schema': [(atom, 'REAL') for atom in
               ['FL', 'FS', 'UL', 'US', 'FLQ', 'FSQ', 'ULQ', 'USQ']],
    'csv_mapping': {
        'clients_in_long': 'LQ',
        'clients_in_lshort': 'SQ',
        'short_position': 'S',
        'long_position': 'L'
    },
    'first_date': dt.date(2012, 11, 1),
    'ct_mapping': {
        'F': 'Futures',
        'C': 'Option call',
        'P': 'Option put'
    },
    'phys_mapping': {
        0: 'U',
        1: 'F'
    },
    'updater': MoexUpdatable
}

