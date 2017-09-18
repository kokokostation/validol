import datetime as dt
from bs4 import BeautifulSoup
from requests_cache import CachedSession
from requests import Request
import pandas as pd

from validol.model.store.resource import Actives, Platforms
from validol.model.store.view.active_info import ActiveInfo
from validol.model.store.structures.pdf_helper import PdfHelpers
from validol.model.store.miners.daily_reports.daily import DailyResource, Cache, NetCache
from validol.model.utils.utils import get_filename, dummy_ctx_mgr
from validol.model.utils.fs_cache import FsCache
from validol.model.store.resource import Updater


class IceDaily:
    def __init__(self, model_launcher, flavor):
        self.model_launcher = model_launcher
        self.flavor = flavor

        self.session_obj = None

    @property
    def session(self):
        if self.session_obj is None:
            self.session_obj = self.prepare_update()

        return self.session_obj

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
        from validol.model.store.miners.daily_reports.ice_view import IceView

        ranges = []

        for index, active in IceActives(self.model_launcher, self.flavor['name']).read_df().iterrows():
            pdf_helper = PdfHelpers(self.model_launcher).read_by_name(
                ActiveInfo(IceView(self.flavor), active.PlatformCode, active.ActiveName))

            ranges.append(Active(self.model_launcher, active.PlatformCode, active.ActiveName,
                                 self.flavor, self, pdf_helper).update())

        return Updater.reduce_ranges(ranges)


class Active(DailyResource):
    def __init__(self, model_launcher, platform_code, active_name, flavor,
                 updater=None, pdf_helper=None):
        DailyResource.__init__(self, model_launcher, platform_code, active_name, IceActives,
                               flavor, pdf_helper)

        self.updater = updater

        self.web_active_code, self.active_code = IceActives(model_launcher, flavor['name'])\
            .get_fields(platform_code, active_name, ('WebActiveCode', 'ActiveCode'))
        self.platform_code = platform_code
        self.flavor = flavor

    class IceCache(NetCache):
        def __init__(self, ice_active):
            self.ice_active = ice_active

        def make_request(self, date):
            request = Request(
                method='POST',
                url='https://www.theice.com/marketdata/reports/datawarehouse/ConsolidatedEndOfDayReportPDF.shtml',
                params={
                    'generateReport': '',
                    'exchangeCode': self.ice_active.platform_code,
                    'exchangeCodeAndContract': self.ice_active.web_active_code,
                    'optionRequest': self.ice_active.flavor['optionRequest'],
                    'selectedDate': date.strftime("%m/%d/%Y"),
                    'submit': 'Download',
                    'smpbss': self.ice_active.updater.session.cookies['smpbss']
                }
            )

            request = self.ice_active.updater.session.prepare_request(request)

            return request

        def get(self, date, with_cache=True):
            request = self.make_request(date)

            with dummy_ctx_mgr() if with_cache else self.ice_active.updater.session.cache_disabled():
                response = self.ice_active.updater.session.send(request)

            if response.content[1:4] != b'PDF':
                self.delete(date)

                return None, None

            return get_filename(response), response.content

        def delete(self, date):
            key = self.ice_active.updater.session.cache.create_key(self.make_request(date))
            self.ice_active.updater.session.cache.delete(key)

        def file(self, date):
            return '{}_{}.pdf'.format(self.ice_active.active_code, date.strftime('%Y_%m_%d'))

    def download_date(self, date):
        content = self.cache.get(date)

        if content is not None:
            try:
                return self.pdf_helper.parse_content(content, date)
            except ValueError:
                self.cache.delete(date)

                return pd.DataFrame()

    def available_dates(self):
        ice_cache = Active.IceCache(self)
        fs_cache = FsCache(self.pdf_helper.active_folder)
        self.cache = Cache(ice_cache, fs_cache)

        with self.updater.session.cache_disabled():
            response = self.updater.session.post(
                url='https://www.theice.com/marketdata/reports/datawarehouse/ConsolidatedEndOfDayReportPDF.shtml',
                headers={
                    'User-Agent': 'Mozilla/5.0',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                params={
                    'selectionForm': '',
                    'exchangeCode': self.platform_code,
                    'optionRequest': self.flavor['optionRequest'],
                    'exchangeCodeAndContract': self.web_active_code,
                    'smpbss': self.updater.session.cookies['smpbss'],
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