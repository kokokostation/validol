import os
from io import BytesIO
from zipfile import ZipFile
import numpy as np
import pandas as pd

from validol.model.store.structures.pdf_helper import PdfParser
from validol.model.store.miners.daily_reports.cme import Active
from validol.model.store.miners.daily_reports.pdf_helpers.utils import filter_rows, expirations
from validol.model.utils import concat


class CmeParser(PdfParser):
    NAME = 'cme'

    def pages(self):
        return [(1, (237.15,16.32,599.76,596.955))], False

    def map_content(self, content):
        with ZipFile(BytesIO(content), 'r') as zip_file:
            return zip_file.read(self.pdf_helper.other_info['archive_file'])

    def process_df(self, df):
        parsing_map = {
            0: 'CONTRACT',
            3: 'SET',
            5: 'CHG',
            6: 'VOL',
            8: 'OI',
            10: 'OIChg'
        }

        df = df.replace({'----': np.NaN})

        for col, sign_col in ((5, 4), (10, 9)):
            if df[col].dtype == np.object:
                df[col] = pd.to_numeric(df[col].replace({'UNCH': 0, 'NEW': np.NaN}))
            df[col] *= df[sign_col].map({'+': 1, '-': -1, np.NaN: 0})

        df = df.rename(columns=parsing_map)[list(parsing_map.values())]

        return filter_rows(df)

    def read_data(self, active_folder):
        from_files = []

        for file in os.listdir(active_folder):
            from_files.append(self.pdf_helper.parse_file(os.path.join(active_folder, file),
                                                         Active.file_to_date(file)))

        return concat(from_files)

    def read_expirations(self, expirations_file):
        return expirations(expirations_file)

