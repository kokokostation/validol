import datetime as dt
from bs4 import BeautifulSoup
from requests_cache import CachedSession
from requests import Request
import pandas as pd
import os
from tempfile import NamedTemporaryFile
import re
import locale
from locale import atof

from validol.model.utils import pdf, to_timestamp, date_range
from validol.model.store.resource import Resource
from validol.model.store.miners.weekly_reports.flavor import Actives, Platforms


class IceActives(Actives):
    def __init__(self, model_launcher):
        Actives.__init__(self, model_launcher, Active.FLAVOR,
                         [
                             ('ActiveCode', 'TEXT'),
                             ('Updatable', 'INTEGER')
                         ])

    def set_update(self, platform_code, active_name, updatable):
        self.dbh.cursor().execute('''
            UPDATE 
                "{table}"
            SET
                Updatable = ?
            WHERE
                PlatformCode = ? AND ActiveName = ?
        '''.format(table=self.table), (updatable, platform_code, active_name))
        self.dbh.commit()


class IceDaily:
    def __init__(self, model_launcher):
        self.model_launcher = model_launcher

    def update_actives(self, df):
        df['Updatable'] = 0
        df['PlatformCode'] = 'IFEU'

        IceActives(self.model_launcher).write_df(df)

    def prepare_update(self):
        platforms_table = Platforms(self.model_launcher, Active.FLAVOR)
        platforms_table.write_df(
            pd.DataFrame([['IFEU', 'ICE FUTURES EUROPE']],
                         columns=("PlatformCode", "PlatformName")))

        session = CachedSession(allowable_methods=('GET', 'POST'),
                                ignored_parameters=['smpbss'])

        with session.cache_disabled():
            response = session.get(
                url='https://www.theice.com/marketdata/reports/datawarehouse/ConsolidatedEndOfDayReportPDF.shtml',
                headers={
                    'User-Agent': 'Mozilla/5.0',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                params={
                    'selectionForm': '',
                    'exchangeCode': 'IFEU',
                    'optionRequest': 'false'
                }
            )

        bs = BeautifulSoup(response.text)

        df = pd.DataFrame([(opt['value'], opt.text) for opt in bs.find_all('option')],
                          columns=["ActiveCode", "ActiveName"])

        self.update_actives(df)

        return session

    def update(self):
        session = self.prepare_update()

        for index, active in IceActives(self.model_launcher).read_df().iterrows():
            if active.Updatable == 1:
                Active(self.model_launcher,
                       active.PlatformCode,
                       active.ActiveName,
                       session).update()


class Active(Resource):
    FLAVOR = 'ice_futures_daily'
    SCHEMA = [
        ('CONTRACT', 'TEXT'),
        ('SET', 'REAL'),
        ('CHG', 'REAL'),
        ('VOL', 'INTEGER'),
        ('OI', 'INTEGER'),
        ('OIChg', 'INTEGER')
    ]
    PARSING_MAP = {
        1: 'CONTRACT',
        6: 'SET',
        7: 'CHG',
        8: 'VOL',
        9: 'OI',
        10: 'OIChg'
    }
    INDEPENDENT = False

    def __init__(self, model_launcher, platform_code, active_name, session=None):
        self.platform_code = platform_code
        self.active_name = active_name
        self.session = session
        self.model_launcher = model_launcher

        self.ice_actives = IceActives(model_launcher)
        active_id, self.active_code = \
            self.ice_actives.get_fields(platform_code, active_name, ('id', 'ActiveCode'))
        platform_id = Platforms(model_launcher, Active.FLAVOR).get_platform_id(platform_code)

        Resource.__init__(
            self,
            model_launcher.main_dbh,
            "Active_platform_{platform_id}_active_{active_id}_{flavor}".format(
                platform_id=platform_id,
                active_id=active_id,
                flavor=Active.FLAVOR),
            Active.SCHEMA,
            "UNIQUE (Date, CONTRACT) ON CONFLICT IGNORE")

    def switch_update(self):
        state = self.ice_actives.get_fields(self.platform_code, self.active_name, ('Updatable',))[0]

        if state == 0:
            self.session = IceDaily(self.model_launcher).prepare_update()
            self.update()

        self.ice_actives.set_update(self.platform_code, self.active_name, 1 - state)

    def download_date(self, date):
        request = Request(
            method='POST',
            url='https://www.theice.com/marketdata/reports/datawarehouse/ConsolidatedEndOfDayReportPDF.shtml',
            params={
                'generateReport': '',
                'exchangeCode': 'IFEU',
                'exchangeCodeAndContract': self.active_code,
                'optionRequest': 'false',
                'selectedDate': date.strftime("%m/%d/%Y"),
                'submit': 'Download',
                'smpbss': self.session.cookies['smpbss']
            }
        )

        request = self.session.prepare_request(request)

        def bad_response():
            key = self.session.cache.create_key(request)
            self.session.cache.delete(key)
            return pd.DataFrame()

        response = self.session.send(request)

        if response.content[1:4] != b'PDF':
            return bad_response()

        with NamedTemporaryFile() as file:
            file.write(response.content)

            try:
                return self.parse_date(file.name, date)
            except ValueError:
                return bad_response()

    def parse_date(self, fname, date):
        df = pdf([
            (1, (135.432, 47.124, 607.662, 752.994)),
            (2, (81.972, 48.114, 601.722, 758.934)),
            (3, (79.002, 51.084, 602.712, 750.024))], fname)
        df = df.rename(str, Active.PARSING_MAP)[list(Active.PARSING_MAP.values())]

        for col in df:
            if df[col].isnull().sum() > 20:
                raise ValueError

        locale.setlocale(locale.LC_NUMERIC, '')

        cols = [a for a, b in Active.SCHEMA if b == 'INTEGER']
        df[cols] = df[cols].applymap(lambda x: atof(str(x)) if not pd.isnull(x) else x)

        df['Date'] = date

        def row_ok(row):
            try:
                dt.datetime.strptime(row['CONTRACT'], '%b%y')
                return True
            except:
                return False

        df = df[df.apply(row_ok, axis=1)]

        return df

    def available_dates(self):
        return [dt.date.today() - dt.timedelta(days=i) for i in range(0, 11)]

    def initial_fill(self):
        dir = 'Ice reports/Futures/'

        from_files = []

        if os.path.isdir(dir):
            pure_active_code = self.active_code.split('|', 1)[1]

            regex = re.compile('{ac}_(\d{{4}}_\d{{2}}_\d{{2}})\.pdf'.format(ac=pure_active_code))

            for file in os.listdir(dir):
                match = regex.match(file)
                if match is not None:
                    from_files.append(
                        self.parse_date(os.path.join(dir, file),
                                        dt.datetime.strptime(match.group(1), '%Y_%m_%d').date()))

        df = pd.concat(from_files + [self.download_date(date) for date in self.available_dates()])

        return df

    def fill(self, first, last):
        return pd.concat([self.download_date(date)
                          for date in set(self.available_dates()) & set(date_range(first, last))])

    def get_flavors(self):
        return pd.read_sql('SELECT DISTINCT CONTRACT AS active_flavor FROM "{table}"'
                           .format(table=self.table), self.dbh)

    def get_flavor(self, contract):
        return pd.read_sql('SELECT * FROM "{table}" WHERE CONTRACT = ?'
                    .format(table=self.table), self.dbh, params=(contract,))