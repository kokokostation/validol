import datetime as dt
import pandas as pd
from ftplib import FTP
import os
from zipfile import ZipFile
from io import BytesIO

from validol.model.store.resource import Actives, Platforms
from validol.model.store.view.active_info import ActiveInfo
from validol.model.store.structures.pdf_helper import PdfHelpers
from validol.model.store.miners.daily_reports.daily import DailyResource
from validol.model.utils import isfile
from validol.model.store.structures.ftp_cache import FtpCache
from validol.model.store.resource import Updater


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

        self.available_dates_cache = None

    @staticmethod
    def file_to_date(file):
        start = len('DailyBulletin_pdf_')
        return dt.datetime.strptime(os.path.basename(file)[start:start + 8], '%Y%m%d').date()

    @staticmethod
    def get_files():
        with FTP(Active.FTP_SERVER) as ftp:
            ftp.login()
            files = [file for file in ftp.nlst(Active.FTP_DIR) if isfile(ftp, file)]

        return files

    @staticmethod
    def read_file(model_launcher, file):
        return FtpCache(model_launcher).read_file(Active.FTP_SERVER, file)

    @staticmethod
    def get_archive_files(model_launcher):
        item = FtpCache(model_launcher).one_or_none()
        if item is None:
            file = Active.get_files()[0]
            item = Active.read_file(model_launcher, file)
        else:
            item = item.value

        with ZipFile(BytesIO(item), 'r') as zip_file:
            return zip_file.namelist()

    def available_dates(self):
        self.available_dates_cache = {Active.file_to_date(file): file for file in Active.get_files()}

        return self.available_dates_cache.keys()

    def download_date(self, date):
        filename = self.available_dates_cache[date]
        content = Active.read_file(self.model_launcher, filename)
        return self.pdf_helper.process_loaded(os.path.basename(filename), content, date)


class CmeActives(Actives):
    def __init__(self, model_launcher, flavor):
        Actives.__init__(self, model_launcher.user_dbh, flavor)