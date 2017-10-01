import datetime as dt
from requests_cache import enabled
import pandas as pd
import re
from io import StringIO
import requests
from dateutil.relativedelta import relativedelta

from validol.model.store.resource import ResourceUpdater
from validol.model.utils.utils import concat


class Expirations(ResourceUpdater):
    SCHEMA = [
        ('Contract', 'TEXT'),
        ('PlatformCode', 'TEXT'),
        ('Event', 'TEXT'),
        ('ActiveCode', 'TEXT'),
        ('ActiveName', 'TEXT'),
        ('Source', 'TEXT')
    ]
    CONSTRAINT = 'UNIQUE (Date, Contract, PlatformCode, Event, ActiveCode, ActiveName) ON CONFLICT IGNORE'
    PLATFORM_RENAME = {'EUROPE': 'IFEU'}

    def __init__(self, model_launcher):
        ResourceUpdater.__init__(self, model_launcher, model_launcher.main_dbh, 'Expirations',
                          Expirations.SCHEMA, Expirations.CONSTRAINT)


    @staticmethod
    def from_contract(date):
        return dt.datetime.strptime(date, '%b%y').date()

    def current(self, ai, delta, df):
        df['CONTRACT'] = df['CONTRACT'].apply(Expirations.from_contract)

        exp = self.model_launcher.get_exp_info(ai)

        exp_info = self.read_df('''
                    SELECT
                        Date, Contract
                    FROM
                        {table}
                    WHERE
                        PlatformCode = ? AND ActiveName = ? AND ActiveCode = ? AND Event = 'LTD'
                ''', params=(exp['PlatformCode'], exp['ActiveName'], exp['ActiveCode']))

        exp_info['Contract'] = exp_info['Contract'].apply(Expirations.from_contract)

        result = pd.DataFrame()

        for i in range(1, len(exp_info)):
            begin, end = exp_info.index[i - 1], exp_info.index[i]

            curr_contract = exp_info['Contract'].iloc[i] + relativedelta(months=delta)

            result = result.append(df[
                (begin < df.index) &
                (df.index <= end) &
                (df.CONTRACT == curr_contract)
                ])

        return result

    def parse_csv(self, csv):
        df = pd.read_csv(StringIO(csv),
                         header=3,
                         parse_dates=['Date'],
                         date_parser=lambda date: dt.datetime.strptime(date, '%d-%b-%Y').date())

        summary = re.compile('(.*?): (.*?):.*')
        description = re.compile('^\s*(.*): (.*) \[(.*)\]$')
        result = pd.DataFrame()

        for i, row in df.iterrows():
            lines = row.Description.split('\n')[1:-1]
            data = []
            for line in lines:
                match = description.match(line)
                data.append([match.group(i) for i in range(1, 4)])

            new_df = pd.DataFrame(data, columns=['Contract', 'ActiveName', 'ActiveCode'])

            new_df['Date'] = row['Date']

            match = summary.match(row.Summary)
            new_df['PlatformCode'] = Expirations.PLATFORM_RENAME.get(match.group(1), match.group(1))
            new_df['Event'] = match.group(2)

            result = result.append(new_df, ignore_index=True)

        result['Source'] = 'net'

        return result

    def fill(self, first, last):
        last += relativedelta(years=7)

        dfs = []

        with enabled():
            while first <= last:
                response = requests.get(
                    url='https://www.theice.com/marketdata/ExpiryCalendar.shtml',
                    params={
                        'excel': '',
                        'markets': (
                            "ICE Futures U.S.",
                            "ICE Futures Europe",
                            "ICE Futures Canada",
                            "ICE OTC",
                            "ICE Trust U.S.",
                            "ICE Clear Europe CDS",
                            "ICE Endex",
                            "ICE Futures Singapore"
                        ),
                        'expirationEnabled': "true",
                        'expirationDates': (
                            "FTD",
                            "LTD",
                            "FDD",
                            "LDD",
                            "FND",
                            "LND",
                            "FSD"
                        ),
                        'dateFrom': first.strftime('%d-%b-%Y')
                    },
                    headers={
                        'User-Agent': 'Mozilla/5.0',
                    }
                )

                first = dt.datetime.strptime(response.text.splitlines()[2][4:], '%d-%b-%Y').date() + dt.timedelta(days=1)

                dfs.append(self.parse_csv(response.text))

        return concat(dfs)

    def initial_fill(self):
        return self.fill(dt.date(2016, 1, 1), dt.date.today())

    def remove_active(self, ai):
        self.dbh.cursor().execute('''
            DELETE 
            FROM 
                "{table}" 
            WHERE
                Source = ?'''.format(table=self.table), (str(ai),))

        self.dbh.commit()

    def get_expirations(self):
        return self.read_df('''
            SELECT DISTINCT
                PlatformCode, ActiveCode, ActiveName
            FROM
                {table}
            ORDER BY
                PlatformCode, ActiveCode
            ''', index_on=False)