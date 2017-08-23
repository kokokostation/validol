import datetime as dt
from requests_cache import enabled
import pandas as pd
import re
from io import StringIO
import requests
from dateutil.relativedelta import relativedelta

from validol.model.store.resource import Resource
from validol.model.utils import concat


class Expirations(Resource):
    SCHEMA = [
        ('Contract', 'TEXT'),
        ('PlatformCode', 'TEXT'),
        ('Event', 'TEXT'),
        ('ActiveCode', 'TEXT'),
        ('ActiveName', 'TEXT'),
    ]
    CONSTRAINT = 'UNIQUE (Date, Contract, PlatformCode, Event, ActiveCode, ActiveName) ON CONFLICT IGNORE'
    PLATFORM_RENAME = {'EUROPE': 'IFEU'}

    def __init__(self, model_launcher):
        Resource.__init__(self, model_launcher.main_dbh, 'Expirations',
                          Expirations.SCHEMA, Expirations.CONSTRAINT)


    @staticmethod
    def from_contract(date):
        return dt.datetime.strptime(date, '%b%y').date()


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