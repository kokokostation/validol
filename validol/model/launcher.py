import os
import sqlite3
import requests
from sqlalchemy import create_engine

from validol.model.store.miners.weekly_reports.flavors import Cftc, Ice
from validol.model.store.view.view_flavors import ALL_VIEW_FLAVORS
from validol.model.resource_manager.resource_manager import ResourceManager
from validol.model.store.miners.monetary import Monetary
from validol.model.store.miners.prices import InvestingPrices
from validol.model.store.structures.atom import Atoms
from validol.model.store.structures.glued_active.glued_active import GluedActives
from validol.model.store.structures.pattern import Patterns, StrPattern
from validol.model.store.structures.table import Tables
from validol.model.store.miners.daily_reports.flavors import DailyReports
from validol.model.store.structures.pdf_helper import PdfHelpers
from validol.model.store.miners.daily_reports.expirations import Expirations
from validol.model.store.collectors.ml import MlCurves, MlCurve


class Update:
    pass

Update.DAILY = [MlCurves] #[DailyReports, Expirations, MlCurves]
Update.WEEKLY = [Monetary, Cftc, Ice] + Update.DAILY


class ModelLauncher:
    def init_user(self, user_db='user.db'):
        self.user_engine = create_engine('sqlite:///{}'.format(user_db))
        self.user_dbh = sqlite3.connect(user_db)

        self.resource_manager = ResourceManager(self)

        return self

    def init_data(self, main_dbh="main.db"):
        if not os.path.exists("data"):
            os.makedirs("data")

        os.chdir("data")

        self.init_user()

        if not os.path.isfile(main_dbh):
            self.main_dbh = sqlite3.connect(":memory:")

            self.update(Update.WEEKLY)

            with sqlite3.connect(main_dbh) as new_db:
                new_db.executescript("".join(self.main_dbh.iterdump()))

        self.main_dbh = sqlite3.connect(main_dbh)

        self.cache_engine = create_engine('sqlite:///cache.sqlite')

        return self

    def update(self, clss):
        try:
            for cls in clss:
                cls(self).update()
            return True
        except requests.exceptions.ConnectionError:
            return False

    def get_prices_info(self, url):
        return InvestingPrices(self).get_info_through_url(url)

    def get_cached_prices(self):
        return InvestingPrices(self).get_prices()

    def get_atoms(self):
        return Atoms(self).get_atoms(ResourceManager.get_primary_atoms())

    def write_atom(self, atom_name, named_formula):
        Atoms(self).write_atom(atom_name, named_formula)

    def remove_atom(self, atom_name):
        Atoms(self).remove_atom(atom_name)

    def get_tables(self):
        return Tables(self).get_tables()

    def get_table(self, table_name):
        return Tables(self).get_table(table_name)

    def write_table(self, table_name, formula_groups):
        Tables(self).write_table(table_name, formula_groups, self.get_atoms())

    def remove_table(self, name):
        Tables(self).remove_table(name)

    def get_patterns(self, table_name):
        return Patterns(self).get_patterns(table_name)

    def get_flavors(self):
        return ALL_VIEW_FLAVORS

    def write_pattern(self, pattern):
        Patterns(self).write_pattern(pattern)

    def remove_pattern(self, pattern):
        Patterns(self).remove(pattern)

    def prepare_tables(self, table_pattern, actives_info, prices_info):
        return self.resource_manager.prepare_tables(table_pattern, actives_info, prices_info)

    def write_glued_active(self, name, actives):
        GluedActives(self).write_active(name, actives)

    def remove_glued_active(self, name):
        GluedActives(self).remove_by_name(name)

    def write_pdf_helper(self, ai, info, other_info):
        PdfHelpers(self).write_helper(ai, info, other_info)

    def read_pdf_helper(self, ai):
        PdfHelpers(self).read_by_name(ai)

    def remove_pdf_helper(self, ai):
        PdfHelpers(self).remove_by_name(ai)

    def get_exp_info(self, ai):
        return PdfHelpers(self).read_by_name(ai).other_info['expirations']

    def read_str_pattern(self, pattern):
        return Patterns(self, StrPattern).read_pattern(pattern.table_name, pattern.name)

    def write_str_pattern(self, pattern):
        return Patterns(self, StrPattern).write_pattern(pattern)

    def get_ml_curves(self, ai, with_flavor=True):
        return MlCurve(self, ai).read_curves(with_flavor)

    def current(self, ai, delta, df):
        return Expirations(self).current(ai, delta, df)