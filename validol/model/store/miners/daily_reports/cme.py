import datetime as dt
import pandas as pd
from ftplib import FTP
import os
from zipfile import ZipFile
from io import BytesIO

from validol.model.store.miners.weekly_reports.flavor import Actives, Platforms
from validol.model.store.view.active_info import ActiveInfo
from validol.model.store.structures.pdf_helper import PdfHelpers
from validol.model.store.miners.daily_reports.daily import DailyResource
from validol.model.utils import isfile
from validol.model.store.structures.ftp_cache import FtpCache


class CmeDaily:
    def __init__(self, model_launcher):
        self.model_launcher = model_launcher

    def update(self):
        platforms_table = Platforms(self.model_launcher, Active.FLAVOR)
        platforms_table.write_df(
            pd.DataFrame([['CME', 'CHICAGO MERCANTILE EXCHANGE']],
                         columns=("PlatformCode", "PlatformName")))

        from validol.model.store.miners.daily_reports.cme_view import CmeView

        for index, active in CmeActives(self.model_launcher).read_df().iterrows():
            pdf_helper = PdfHelpers(self.model_launcher).read_by_name(
                ActiveInfo(CmeView(), active.PlatformCode, active.ActiveName))

            Active(self.model_launcher,
                   active.PlatformCode,
                   active.ActiveName,
                   pdf_helper).update()


class Active(DailyResource):
    FLAVOR = 'cme_daily'
    FTP_SERVER = 'ftp.cmegroup.com'
    FTP_DIR = 'pub/bulletin/'

    def __init__(self, model_launcher, platform_code, active_name, pdf_helper=None):
        DailyResource.__init__(self, model_launcher, platform_code, active_name, CmeActives,
                               Active.FLAVOR, pdf_helper)

        self.available = None

    @staticmethod
    def file_to_date(file):
        start = len(os.path.join(Active.FTP_DIR, 'DailyBulletin_pdf_'))
        return dt.datetime.strptime(file[start:start + 8], '%Y%m%d').date()

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
        self.available = {Active.file_to_date(file): file for file in Active.get_files()}

        return self.available.keys()

    def download_date(self, date):
        content = Active.read_file(self.model_launcher, self.available[date])
        return self.pdf_helper.parse_content(content, date)


class CmeActives(Actives):
    def __init__(self, model_launcher, flavor=Active.FLAVOR):
        Actives.__init__(self, model_launcher.user_dbh, flavor)