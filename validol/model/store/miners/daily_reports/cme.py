import datetime as dt
import pandas as pd
from ftplib import FTP
import os
from zipfile import ZipFile
from io import BytesIO

from validol.model.store.resource import Actives, Platforms
from validol.model.store.view.active_info import ActiveInfo
from validol.model.store.structures.pdf_helper import PdfHelpers
from validol.model.store.miners.daily_reports.daily import DailyResource, Cache, NetCache
from validol.model.utils.utils import isfile
from validol.model.store.structures.ftp_cache import FtpCache
from validol.model.store.resource import Updater
from validol.model.utils.fs_cache import FsCache


class CmeDaily:
    def __init__(self, model_launcher, flavor):
        self.model_launcher = model_launcher
        self.flavor = flavor

    def update(self):
        platforms_table = Platforms(self.model_launcher, self.flavor['name'])
        platforms_table.write_df(
            pd.DataFrame([['CME', 'CHICAGO MERCANTILE EXCHANGE']],
                         columns=("PlatformCode", "PlatformName")))

        from validol.model.store.miners.daily_reports.cme_view import CmeView

        ranges = []

        for index, active in CmeActives(self.model_launcher, self.flavor['name']).read_df().iterrows():
            pdf_helper = PdfHelpers(self.model_launcher).read_by_name(
                ActiveInfo(CmeView(self.flavor), active.PlatformCode, active.ActiveName))

            ranges.append(Active(self.model_launcher, active.PlatformCode, active.ActiveName,
                                 self.flavor, pdf_helper).update())

        return Updater.reduce_ranges(ranges)


class Active(DailyResource):
    FTP_SERVER = 'ftp.cmegroup.com'
    FTP_DIR = 'pub/bulletin/'

    def __init__(self, model_launcher, platform_code, active_name, flavor, pdf_helper=None):
        DailyResource.__init__(self, model_launcher, platform_code, active_name, CmeActives,
                               flavor, pdf_helper)

    class CmeCache(NetCache):
        def __init__(self, cme_active, fs_cache):
            self.cme_active = cme_active

            self.available_dates = {Active.CmeCache.file_to_date(file): file
                                    for file in Active.CmeCache.get_files() +
                                    fs_cache.get_filenames()}

        @staticmethod
        def file_to_date(file):
            start = len('DailyBulletin_pdf_')
            return dt.datetime.strptime(file[start:start + 8], '%Y%m%d').date()

        @staticmethod
        def get_files():
            with FTP(Active.FTP_SERVER) as ftp:
                ftp.login()
                ftp.cwd(Active.FTP_DIR)
                files = [file for file in ftp.nlst() if isfile(ftp, file)]

            return files

        @staticmethod
        def read_file(model_launcher, filename, with_cache=True):
            return FtpCache(model_launcher) \
                .get(Active.FTP_SERVER, os.path.join(Active.FTP_DIR, filename), with_cache)

        def file(self, handle):
            return self.available_dates[handle]

        def get(self, handle, with_cache):
            filename = self.file(handle)
            return filename, Active.CmeCache.read_file(self.cme_active.model_launcher, filename, with_cache)

    @staticmethod
    def get_archive_files(model_launcher):
        item = FtpCache(model_launcher).one_or_none()
        if item is None:
            file = Active.CmeCache.get_files()[0]
            item = Active.CmeCache.read_file(model_launcher, file)
        else:
            item = item.value

        with ZipFile(BytesIO(item), 'r') as zip_file:
            return zip_file.namelist()

    def available_dates(self):
        fs_cache = FsCache(self.pdf_helper.active_folder)
        cme_cache = Active.CmeCache(self, fs_cache)
        self.cache = Cache(cme_cache, fs_cache)

        return cme_cache.available_dates.keys()

    def download_date(self, date):
        content = self.cache.get(date)
        return self.pdf_helper.parse_content(content, date)


class CmeActives(Actives):
    def __init__(self, model_launcher, flavor):
        Actives.__init__(self, model_launcher.user_dbh, flavor)