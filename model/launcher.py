import os
import sqlite3
import pandas as pd

import requests

from model.resource_manager.resource_manager import ResourceManager
from model.store.collectors.monetary_delta import MonetaryDelta
from model.store.miners.flavors import Cftc, Ice
from model.store.miners.flavor import Platforms, Actives
from model.store.miners.monetary import Monetary
from model.store.miners.prices import InvestingPrices
from model.store.structures.atom import Atoms
from model.store.structures.pattern import Patterns
from model.store.structures.table import Tables
from model.store.miners.flavors import FLAVORS_MAP, GLUED_ACTIVE
from model.store.structures.glued_active import GluedActives


class ModelLauncher:
    def __init__(self):
        initial = False
        if not os.path.exists("data"):
            os.makedirs("data")
            initial = True

        os.chdir("data")

        self.dbh = sqlite3.connect("main.db")

        if initial:
            for cls in (Atoms, Tables, Patterns, GluedActives):
                with open(cls().file_name, "a+"):
                    pass

            self.update()

        self.resource_manager = ResourceManager(self)

    def update(self):
        try:
            for cls in (Monetary, MonetaryDelta, Cftc, Ice):
                cls(self.dbh).update()
            return True
        except requests.exceptions.ConnectionError:
            return False

    def get_prices_info(self, url):
        return InvestingPrices(self.dbh).get_info_through_url(url)

    def get_cached_prices(self):
        return InvestingPrices(self.dbh).get_prices()

    def get_platforms(self, flavor):
        if flavor == GLUED_ACTIVE["name"]:
            return pd.DataFrame([["GA", "Glued actives"]], columns=["PlatformCode", "PlatformName"])
        else:
            return Platforms(self.dbh, FLAVORS_MAP[flavor]).get_platforms()

    def get_actives(self, platform, flavor):
        if flavor == GLUED_ACTIVE["name"]:
            return GluedActives().get_actives()
        else:
            return Actives(self.dbh, FLAVORS_MAP[flavor]).get_actives(platform)

    def get_atoms(self):
        return Atoms().get_atoms(self.resource_manager.get_primary_atoms())

    def write_atom(self, atom_name, named_formula):
        Atoms().write_atom(atom_name, named_formula, self.get_atoms())

    def remove_atom(self, atom_name):
        Atoms().remove_atom(atom_name)

    def get_tables(self):
        return Tables().get_tables()

    def write_table(self, table_name, formula_groups):
        Tables().write_table(table_name, formula_groups)

    def remove_table(self, name):
        Tables().remove_by_name(name)

    def get_patterns(self, table_name):
        return Patterns().get_patterns(table_name)

    def get_flavors(self):
        return list(FLAVORS_MAP.values())

    def write_pattern(self, pattern):
        Patterns().write_pattern(pattern)

    def remove_pattern(self, table_name, pattern_name):
        Patterns().remove_pattern(table_name, pattern_name)

    def prepare_tables(self, table_pattern, actives_info, prices_info):
        return self.resource_manager.prepare_tables(table_pattern, actives_info, prices_info)

    def write_glued_active(self, name, actives):
        GluedActives().write_active(name, actives)

    def remove_glued_active(self, name):
        GluedActives().remove_by_name(name)
