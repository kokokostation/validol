import os
import sqlite3

import pandas as pd
import requests
from sqlalchemy import create_engine
from validol.model.store.miners.weekly_reports.flavors import Cftc, Ice
from validol.model.store.view.view_flavor import all_view_flavors

from validol.model.resource_manager.resource_manager import ResourceManager
from validol.model.store.collectors.monetary_delta import MonetaryDelta
from validol.model.store.miners.monetary import Monetary
from validol.model.store.miners.prices import InvestingPrices
from validol.model.store.miners.weekly_reports.flavor import Platforms, Actives
from validol.model.store.structures.atom import Atoms
from validol.model.store.structures.glued_active import GluedActives
from validol.model.store.structures.pattern import Patterns
from validol.model.store.structures.table import Tables


class ModelLauncher:
    def init_user(self):
        self.user_dbh = create_engine('sqlite:///user.db')

        self.resource_manager = ResourceManager(self)

        return self

    def init_data(self):
        if not os.path.exists("data"):
            os.makedirs("data")

        os.chdir("data")

        initial = not os.path.isfile("main.db")

        self.main_dbh = sqlite3.connect("main.db")
        self.init_user()

        if initial:
            self.update()

        return self

    def update(self):
        try:
            for cls in (Monetary, MonetaryDelta, Cftc, Ice):
                cls(self).update()
            return True
        except requests.exceptions.ConnectionError:
            return False

    def get_prices_info(self, url):
        return InvestingPrices(self).get_info_through_url(url)

    def get_cached_prices(self):
        return InvestingPrices(self).get_prices()

    def get_atoms(self):
        return Atoms(self).get_atoms(self.resource_manager.get_primary_atoms())

    def write_atom(self, atom_name, named_formula):
        Atoms(self).write_atom(atom_name, named_formula, self.get_atoms())

    def remove_atom(self, atom_name):
        Atoms(self).remove_atom(atom_name)

    def get_tables(self):
        return Tables(self).get_tables()

    def get_table(self, table_name):
        return Tables(self).get_table(table_name)

    def write_table(self, table_name, formula_groups):
        Tables(self).write_table(table_name, formula_groups)

    def remove_table(self, name):
        Tables(self).remove_table(name)

    def get_patterns(self, table_name):
        return Patterns(self).get_patterns(table_name)

    def get_flavors(self):
        return all_view_flavors(self)

    def write_pattern(self, pattern):
        Patterns(self).write_pattern(pattern)

    def remove_pattern(self, table_name, pattern_name):
        Patterns(self).remove_pattern(table_name, pattern_name)

    def prepare_tables(self, table_pattern, actives_info, prices_info):
        return self.resource_manager.prepare_tables(table_pattern, actives_info, prices_info)

    def write_glued_active(self, name, actives):
        GluedActives(self).write_active(name, actives)

    def remove_glued_active(self, name):
        GluedActives(self).remove_by_name(name)