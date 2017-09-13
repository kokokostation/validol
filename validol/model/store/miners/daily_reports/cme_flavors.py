from validol.model.store.miners.daily_reports.ice_flavors import OPTIONS_SCHEMA, \
    FUTURES_SCHEMA, OPTIONS_CONSTRAINT, FUTURES_CONSTRAINT
from validol.model.store.miners.daily_reports.pdf_helpers.cme import CmeFuturesParser, CmeOptionsParser
from validol.model.store.miners.daily_reports.cme import CmeDaily
from validol.model.store.miners.daily_reports.cme_view import CmeView

CME_FUTURES = {
    'name': 'cme_daily',
    'schema': FUTURES_SCHEMA,
    'processors': [CmeFuturesParser],
    'constraint': FUTURES_CONSTRAINT,
    'get_df': True,
    'options': False,
    'updater': CmeDaily,
    'view': CmeView
}

CME_OPTIONS = {
    'name': 'cme_daily_options',
    'schema': OPTIONS_SCHEMA,
    'processors': [CmeOptionsParser],
    'constraint': OPTIONS_CONSTRAINT,
    'get_df': False,
    'options': True,
    'updater': CmeDaily,
    'view': CmeView,
    'atoms_donor': False
}

CME_DAILY_FLAVORS = [CME_FUTURES, CME_OPTIONS]