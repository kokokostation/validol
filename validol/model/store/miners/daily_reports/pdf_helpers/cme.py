import os
from io import BytesIO
from zipfile import ZipFile
import numpy as np
import pandas as pd
from itertools import repeat
import re

from validol.model.store.miners.daily_reports.cme import Active
from validol.model.store.miners.daily_reports.pdf_helpers.utils import filter_rows, DailyPdfParser, is_contract
from validol.model.utils.utils import concat, get_pages_run


class CmeParser(DailyPdfParser):
    @staticmethod
    def split_info(df):
        return df.iloc[0, :], df.iloc[1:, :].reset_index(drop=True)

    def map_content(self, content):
        with ZipFile(BytesIO(content), 'r') as zip_file:
            return zip_file.read(self.pdf_helper.other_info['archive_file'])

    def read_data(self, active_folder):
        from_files = []

        for file in os.listdir(active_folder):
            from_files.append(self.pdf_helper.parse_file(os.path.join(active_folder, file),
                                                         Active.file_to_date(file)))

        return concat(from_files)

    def pages(self, content):
        return [(zip(get_pages_run(BytesIO(content), self.pdf_helper.name.active),
                   repeat(self.config['page_area'])),
                {'guess': False, 'pandas_options': {'header': None}, 'columns': self.config['columns']},
                 lambda x: x)]

    def process_df(self, pdf_df):
        pdf_df = pdf_df[~pdf_df[0].str.contains('TOTAL').fillna(False)].reset_index(drop=True)

        headers = pdf_df[pdf_df[0].str.contains(self.config['header_regex']).fillna(False)].index.tolist()

        result = pd.DataFrame()

        for section in np.split(pdf_df, headers)[1:]:
            head, section = CmeParser.split_info(section)

            result = result.append(self.process_section(head, section))

        return result

    def get_config(self):
        raise NotImplementedError

    def process_section(self, head, section):
        raise NotImplementedError


class CmeFuturesParser(CmeParser):
    NAME = 'cme'

    def process_section(self, head, section):
        if head[1] == self.pdf_helper.name.active:
            parsing_map = {
                0: 'CONTRACT',
                2: 'SET',
                3: 'CHG',
                4: 'VOL',
                6: 'OI',
                7: 'OIChg'
            }

            section = section.rename(columns=parsing_map)[list(parsing_map.values())]

            section = section.replace({'----': np.NaN})

            for col in ('CHG', 'OIChg'):
                if section[col].dtype == np.object:
                    section[col] = section[col].apply(lambda s: s.replace(' ', ''))
                    section[col] = pd.to_numeric(section[col].replace({'UNCH': 0, 'NEW': np.NaN}))

            return filter_rows(section)
        else:
            return pd.DataFrame()

    def get_config(self):
        return {
            'columns': (92.82, 265.71, 314.67, 378.93, 440.13, 504.39, 558.705),
            'page_area': (133.11, 15.555, 969.255, 596.955),
            'header_regex': 'FUT',
            'exp_prefix': DailyPdfParser.FUTURES_EXP_PREFIX,
            'exp_types': DailyPdfParser.FUTURES_EXP_TYPES
        }


class CmeOptionsParser(CmeParser):
    NAME = 'cme_options'

    def process_section(self, head, section):
        if head[2] == self.pdf_helper.name.active:
            pc = 'P' if re.match('^.*PUT$', head[0]) else 'C'

            section_result = pd.DataFrame()
            contracts = section[section[0].apply(is_contract)].index.tolist()
            for contract in np.split(section, contracts)[1:]:
                head, contract = CmeParser.split_info(contract)

                contract_info = pd.DataFrame()
                contract_info['STRIKE'] = pd.to_numeric(contract[0].apply(lambda s: s.split()[0])) / 100
                contract_info['OI'] = pd.to_numeric(contract[3])
                contract_info['CONTRACT'] = head[0]

                section_result = section_result.append(contract_info)

            section_result['PC'] = pc

            return section_result
        else:
            return pd.DataFrame()

    def get_config(self):
        return {
            'columns': (45.39, 76.755, 528.87, 563.295),
            'page_area': (196.605, 5.61, 977.67, 608.43),
            'header_regex': 'CALL|PUT',
            'exp_prefix': DailyPdfParser.OPTIONS_EXP_PREFIX,
            'exp_types': DailyPdfParser.OPTIONS_EXP_TYPES
        }
