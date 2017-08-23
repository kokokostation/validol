import pandas as pd
import datetime as dt
import os
import re
import locale
from locale import atof

from validol.model.store.structures.pdf_helper import PdfParser
from validol.model.store.miners.daily_reports.ice import Active
from validol.model.store.miners.daily_reports.pdf_helpers.utils import filter_rows, expirations
from validol.model.utils import concat


class IceParser(PdfParser):
    NAME = 'ice'

    def pages(self):
        return [
            (1, (135.432, 47.124, 607.662, 752.994)),
            (2, (81.972, 48.114, 601.722, 758.934)),
            (3, (79.002, 51.084, 602.712, 750.024))
        ], True

    def process_df(self, df):
        parsing_map = {
            1: 'CONTRACT',
            6: 'SET',
            7: 'CHG',
            8: 'VOL',
            9: 'OI',
            10: 'OIChg'
        }

        df = df.rename(columns=parsing_map)[list(parsing_map.values())]

        for col in df:
            if df[col].isnull().sum() > 20:
                raise ValueError

        locale.setlocale(locale.LC_NUMERIC, '')

        cols = [a for a, b in Active.SCHEMA if b == 'INTEGER']
        df[cols] = df[cols].applymap(lambda x: atof(str(x)) if not pd.isnull(x) else x)

        return filter_rows(df)

    def read_expirations(self, expirations_file):
        return expirations(expirations_file)

    def read_data(self, active_folder):
        from_files = []

        pure_active_code = self.pdf_helper.other_info['active_code']

        regex = re.compile('{ac}_(\d{{4}}(?:_\d{{2}}){{2}})\.pdf'.format(ac=pure_active_code))

        for file in os.listdir(active_folder):
            match = regex.match(file)
            if match is not None:
                from_files.append(
                    self.pdf_helper.parse_file(
                        os.path.join(active_folder, file),
                        dt.datetime.strptime(match.group(1), '%Y_%m_%d').date()))

        return concat(from_files)

