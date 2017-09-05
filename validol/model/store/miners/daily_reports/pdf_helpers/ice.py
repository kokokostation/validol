import pandas as pd
import datetime as dt
import os
import re
import locale
from locale import atof

from validol.model.store.miners.daily_reports.pdf_helpers.utils import filter_rows, DailyPdfParser
from validol.model.utils import concat


class IceParser(DailyPdfParser):
    def parsing_map(self):
        raise NotImplementedError

    def pages(self, content):
        return [('all', None)], {'lattice': True, 'pandas_options': {'header': None}}

    def process_df(self, df):
        df = filter_rows(df.rename(columns=self.parsing_map())[list(self.parsing_map().values())])

        for col in df:
            if df[col].isnull().sum() > 20:
                raise ValueError

        locale.setlocale(locale.LC_NUMERIC, '')

        from validol.model.store.miners.daily_reports.ice_flavors import ICE_DAILY_FLAVORS_MAP
        schema = ICE_DAILY_FLAVORS_MAP[self.pdf_helper.name.flavor.name()]['schema']

        cols = [a for a, b in schema if b == 'INTEGER']
        df[cols] = df[cols].applymap(lambda x: atof(str(x)) if not pd.isnull(x) else x)

        return df

    def fix_df(self, df):
        return df

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


class IceFuturesParser(IceParser):
    NAME = 'ice'

    def parsing_map(self):
        return {
            1: 'CONTRACT',
            6: 'SET',
            7: 'CHG',
            8: 'VOL',
            9: 'OI',
            10: 'OIChg'
        }

    def get_config(self):
        return {
            'exp_prefix': DailyPdfParser.FUTURES_EXP_PREFIX,
            'exp_types': DailyPdfParser.FUTURES_EXP_TYPES
        }


class IceOptionsParser(IceParser):
    NAME = 'ice_options'

    def parsing_map(self):
        return {
            1: 'CONTRACT',
            2: 'STRIKE',
            3: 'PC',
            12: 'OI'
        }

    def get_config(self):
        return {
            'exp_prefix': DailyPdfParser.OPTIONS_EXP_PREFIX,
            'exp_types': DailyPdfParser.OPTIONS_EXP_TYPES
        }