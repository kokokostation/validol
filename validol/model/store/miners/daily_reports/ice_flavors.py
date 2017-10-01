from validol.model.store.miners.daily_reports.pdf_helpers.ice import IceFuturesParser, \
    IceOptionsParser
from validol.model.store.miners.daily_reports.ice import IceDaily
from validol.model.store.miners.daily_reports.ice_view import IceView

OPTIONS_SCHEMA = [
    ('CONTRACT', 'TEXT'),
    ('STRIKE', 'REAL'),
    ('PC', 'TEXT'),
    ('OI', 'INTEGER')
]
FUTURES_SCHEMA = [
    ('CONTRACT', 'TEXT'),
    ('SET', 'REAL'),
    ('CHG', 'REAL'),
    ('VOL', 'INTEGER'),
    ('OI', 'INTEGER'),
    ('OIChg', 'INTEGER')
]

FUTURES_CONSTRAINT = "UNIQUE (Date, CONTRACT) ON CONFLICT REPLACE"
OPTIONS_CONSTRAINT = "UNIQUE (Date, CONTRACT, STRIKE, PC) ON CONFLICT REPLACE"

ICE_FUTURES = {
    'name': 'ice_daily',
    'optionRequest': 'false',
    'processors': [IceFuturesParser],
    'schema': FUTURES_SCHEMA,
    'constraint': FUTURES_CONSTRAINT,
    'get_df': True,
    'options': False,
    'updater': IceDaily,
    'view': IceView
}

ICE_OPTIONS = {
    'name': 'ice_daily_options',
    'optionRequest': 'true',
    'processors': [IceOptionsParser],
    'schema': OPTIONS_SCHEMA,
    'constraint':OPTIONS_CONSTRAINT,
    'get_df': False,
    'options': True,
    'updater': IceDaily,
    'view': IceView,
    'atoms_donor': False
}

ICE_DAILY_FLAVORS = [ICE_OPTIONS, ICE_FUTURES]
ICE_DAILY_FLAVORS_MAP = {flavor['name']: flavor for flavor in ICE_DAILY_FLAVORS}