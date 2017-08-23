import pandas as pd
import datetime as dt

from validol.model.store.miners.daily_reports.expirations import Expirations


def row_ok(row):
    try:
        Expirations.from_contract(row['CONTRACT'])
        return True
    except:
        return False


def filter_rows(df):
    return df[df.apply(row_ok, axis=1)]


def date_parser(date):
    for fmt in ['%m/%d/%Y', '%m/%d/%y']:
        try:
            return dt.datetime.strptime(date, fmt).date()
        except ValueError:
            pass


def expirations(expirations_file):
    result = pd.DataFrame()
    types = ['FTD', 'LTD', 'FND', 'LND', 'FSD']

    df = pd.read_csv(expirations_file, parse_dates=types, date_parser=date_parser) \
        .rename(columns={'CONTRACT SYMBOL': 'Contract'})

    for t in types:
        new = df[['Contract', t]].rename(columns={t: 'Date'})
        new['Event'] = t

        result = result.append(new)

    return result