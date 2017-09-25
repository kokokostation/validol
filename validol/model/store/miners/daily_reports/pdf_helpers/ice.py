import pandas as pd
import datetime as dt
import os
import re

from validol.model.store.miners.daily_reports.pdf_helpers.utils import filter_rows, DailyPdfParser
from validol.model.utils.utils import concat


class IceParser(DailyPdfParser):
    def parsing_map(self):
        raise NotImplementedError

    def config(self, content):
        name_processor = {
            'kwargs': {'lattice': True},
            'postprocessor': lambda df: pd.DataFrame([df.iloc[i].name for i in range(len(df))])
        }

        plain_processor = {
            'kwargs': {'lattice': True, 'pandas_options': {'header': None}}
        }

        processors = [plain_processor, name_processor]

        return [
            {
                'pages': [('all', None)],
                'processors': processors
            },
            {
                'pages': [('start-end', None)],
                'processors': processors
            }
        ]

    def process_df(self, df):
        df = filter_rows(df.rename(columns=self.parsing_map())[list(self.parsing_map().values())])

        for col in df:
            if df[col].isnull().sum() > 20:
                raise ValueError

        from validol.model.store.miners.daily_reports.ice_flavors import ICE_DAILY_FLAVORS_MAP
        schema = ICE_DAILY_FLAVORS_MAP[self.pdf_helper.name.flavor.name()]['schema']

        cols = [a for a, b in schema if b == 'INTEGER']
        df[cols] = df[cols].applymap(lambda x: int(str(x).replace(',', '')) if not pd.isnull(x) else x)

        return df

    def fix_df(self, df):
        return df


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