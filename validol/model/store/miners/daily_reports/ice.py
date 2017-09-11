import datetime as dt
from bs4 import BeautifulSoup
from requests_cache import CachedSession
from requests import Request
import pandas as pd

from validol.model.store.resource import Actives, Platforms
from validol.model.store.view.active_info import ActiveInfo
from validol.model.store.structures.pdf_helper import PdfHelpers
from validol.model.store.miners.daily_reports.daily import DailyResource
from validol.model.utils import get_filename


class IceDaily:
    def __init__(self, model_launcher, flavor):
        self.model_launcher = model_launcher
        self.flavor = flavor

    def update_actives(self, df):
        df['PlatformCode'] = 'IFEU'

        IceAllActives(self.model_launcher, self.flavor['name']).write_df(df)

    def prepare_update(self):
        platforms_table = Platforms(self.model_launcher, self.flavor['name'])
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
                    'optionRequest': self.flavor['optionRequest']
                }
            )

        bs = BeautifulSoup(response.text)

        df = pd.DataFrame([(opt['value'], opt.text) for opt in bs.find_all('option')],
                          columns=["WebActiveCode", "ActiveName"])

        df['ActiveCode'] = df.WebActiveCode.apply(lambda s: s.split('|', 1)[1] if '|' in s else None)
        df = df.dropna(how='any')

        self.update_actives(df)

        return session

    def update(self):
        session = self.prepare_update()

        from validol.model.store.miners.daily_reports.ice_view import IceView

        for index, active in IceActives(self.model_launcher, self.flavor['name']).read_df().iterrows():
            pdf_helper = PdfHelpers(self.model_launcher).read_by_name(
                ActiveInfo(IceView(self.flavor), active.PlatformCode, active.ActiveName))

            Active(self.model_launcher, active.PlatformCode, active.ActiveName, self.flavor,
                   session, pdf_helper).update()


class Active(DailyResource):
    def __init__(self, model_launcher, platform_code, active_name, flavor,
                 session=None, pdf_helper=None):
        DailyResource.__init__(self, model_launcher, platform_code, active_name, IceActives,
                               flavor, pdf_helper)

        self.session = session

        self.active_code = IceActives(model_launcher, flavor['name'])\
            .get_fields(platform_code, active_name, ('WebActiveCode',))[0]
        self.platform_code = platform_code
        self.flavor = flavor

    def download_date(self, date):
        request = Request(
            method='POST',
            url='https://www.theice.com/marketdata/reports/datawarehouse/ConsolidatedEndOfDayReportPDF.shtml',
            params={
                'generateReport': '',
                'exchangeCode': self.platform_code,
                'exchangeCodeAndContract': self.active_code,
                'optionRequest': self.flavor['optionRequest'],
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

        try:
            return self.pdf_helper.process_loaded(get_filename(response), response.content, date)
        except ValueError:
            return bad_response()

    def available_dates(self):
        with self.session.cache_disabled():
            response = self.session.post(
                url='https://www.theice.com/marketdata/reports/datawarehouse/ConsolidatedEndOfDayReportPDF.shtml',
                headers={
                    'User-Agent': 'Mozilla/5.0',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                params={
                    'selectionForm': '',
                    'exchangeCode': self.platform_code,
                    'optionRequest': self.flavor['optionRequest'],
                    'exchangeCodeAndContract': self.active_code,
                    'smpbss': self.session.cookies['smpbss'],
                }
            )

        bs = BeautifulSoup(response.text)

        return [dt.datetime.strptime(a['value'][4:-17] + a['value'][-4:], '%b %d %Y').date()
                for a in bs.find_all(attrs={'name': "selectedDate"})]


class IceActives(Actives):
    def __init__(self, model_launcher, flavor):
        Actives.__init__(self, model_launcher.user_dbh, flavor, [
            ('ActiveCode', 'TEXT'),
            ('WebActiveCode', 'TEXT')
        ])


class IceAllActives(IceActives):
    def __init__(self, model_launcher, flavor):
        IceActives.__init__(self, model_launcher, "all_{}".format(flavor))