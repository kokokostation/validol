import datetime as dt
from ftplib import FTP
import os
from zipfile import ZipFile
from io import BytesIO
from functools import lru_cache
import re

from validol.model.store.resource import Actives, Platforms
from validol.model.store.view.active_info import ActiveInfo
from validol.model.store.miners.daily_reports.daily import DailyResource, NetCache
from validol.model.utils.utils import isfile
from validol.model.store.structures.ftp_cache import FtpCache
from validol.model.store.utils import reduce_ranges


class CmeDaily:
    def __init__(self, model_launcher, flavor):
        self.model_launcher = model_launcher
        self.flavor = flavor

    def update(self):
        platforms_table = Platforms(self.model_launcher, self.flavor['name'])
        platforms_table.write_single('CME', 'CHICAGO MERCANTILE EXCHANGE')

        from validol.model.store.miners.daily_reports.cme_view import CmeView

        ranges = []
        adc = Active.Cache.make_available_dates_cache()

        for index, active in CmeActives(self.model_launcher, self.flavor['name']).read_df().iterrows():
            pdf_helper = self.model_launcher.read_pdf_helper(
                ActiveInfo(CmeView(self.flavor), active.PlatformCode, active.ActiveName))

            ranges.append(Active(self.model_launcher, active.PlatformCode, active.ActiveName,
                                 self.flavor, pdf_helper, adc).update())

        return reduce_ranges(ranges)


class Active(DailyResource):
    FTP_SERVER = 'ftp.cmegroup.com'
    FTP_DIR = 'pub/bulletin/'

    def __init__(self, model_launcher, platform_code, active_name, flavor, pdf_helper=None, adc=None):
        DailyResource.__init__(self, model_launcher, platform_code, active_name, CmeActives,
                               flavor, pdf_helper, Active.Cache(self, adc))

    class Cache(NetCache):
        def __init__(self, cme_active, adc=None):
            self.cme_active = cme_active
            self.adc = adc

        @staticmethod
        def if_valid_zip(file):
            return re.match('^DailyBulletin_pdf_\d+\.zip$', file) is not None

        @property
        @lru_cache()
        def available_dates_cache(self):
            return Active.Cache.make_available_dates_cache() if self.adc is None else self.adc

        @staticmethod
        def make_available_dates_cache():
            files = Active.Cache.get_files()

            return {handle: file for handle, file in
                    zip(map(Active.Cache.handle_helper, files), files) if handle is not None}

        @staticmethod
        def handle_helper(file):
            if not Active.Cache.if_valid_zip(file):
                return None

            start = len('DailyBulletin_pdf_')
            try:
                return dt.datetime.strptime(file[start:start + 8], '%Y%m%d').date()
            except:
                return None

        def handle(self, file):
            return Active.Cache.handle_helper(file)

        @staticmethod
        def get_files():
            try:
                with FTP(Active.FTP_SERVER) as ftp:
                    ftp.login()
                    ftp.cwd(Active.FTP_DIR)
                    files = [file for file in ftp.nlst() if isfile(ftp, file)]

                return files
            except Exception as e:
                print(e)

                return []

        @staticmethod
        def read_file(model_launcher, filename, with_cache=True):
            return FtpCache(model_launcher) \
                .get(Active.FTP_SERVER, os.path.join(Active.FTP_DIR, filename), with_cache)

        def file(self, handle):
            return self.available_dates_cache.get(handle, None)

        def get(self, handle, with_cache):
            filename = self.file(handle)
            if filename is None:
                return None, None

            try:
                return filename, Active.Cache.read_file(self.cme_active.model_launcher, filename, with_cache)
            except Exception as e:
                print(e)

                return None, None

        def available_handles(self):
            return self.available_dates_cache.keys()

        def delete(self, date):
            file = self.available_dates_cache.get(date, None)
            if file is not None:
                FtpCache(self.cme_active.model_launcher).remove_by_name(file)

    @staticmethod
    def get_archive_files(model_launcher):
        item = FtpCache(model_launcher).one_or_none()
        if item is None:
            file = Active.Cache.get_files()[0]
            item = Active.Cache.read_file(model_launcher, file)
        else:
            item = item.value

        with ZipFile(BytesIO(item), 'r') as zip_file:
            return zip_file.namelist()


class CmeActives(Actives):
    def __init__(self, model_launcher, flavor):
        Actives.__init__(self, model_launcher.user_dbh, flavor)