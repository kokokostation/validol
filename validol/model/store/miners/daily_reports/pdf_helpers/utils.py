import pandas as pd
import datetime as dt

from validol.model.store.miners.daily_reports.expirations import Expirations
from validol.model.store.structures.pdf_helper import PdfParser


def is_contract(entry):
    try:
        Expirations.from_contract(entry)
        return True
    except:
        return False


def filter_rows(df):
    return df[df['CONTRACT'].apply(is_contract)]


def date_parser(date):
    for fmt in ['%m/%d/%Y', '%m/%d/%y']:
        try:
            return dt.datetime.strptime(date, fmt).date()
        except ValueError:
            pass


class DailyPdfParser(PdfParser):
    FUTURES_EXP_TYPES = ['FTD', 'LTD', 'FND', 'LND', 'FSD']
    FUTURES_EXP_PREFIX = '{}'
    OPTIONS_EXP_TYPES = ['FTD', 'LTD']
    OPTIONS_EXP_PREFIX = 'OPTIONS {}'

    def __init__(self, pdf_helper):
        PdfParser.__init__(self, pdf_helper)

        self.parser_config = self.get_config()

    def get_config(self):
        raise NotImplementedError

    def read_expirations(self, expirations_file):
        result = pd.DataFrame()

        types = [self.parser_config['exp_prefix'].format(tp) for tp in self.parser_config['exp_types']]

        df = pd.read_csv(expirations_file, parse_dates=types, date_parser=date_parser) \
            .rename(columns={'CONTRACT SYMBOL': 'Contract'})

        for tp, true_tp in zip(types, self.parser_config['exp_types']):
            new = df[['Contract', tp]].rename(columns={tp: 'Date'})
            new['Event'] = true_tp

            result = result.append(new)

        result['Source'] = self.pdf_helper.name.active_only()

        return result[pd.notnull(result.Date)]