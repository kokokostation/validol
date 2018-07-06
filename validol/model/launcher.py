import os
import sqlite3
from sqlalchemy import create_engine
import socket
import socks
import json

from validol.model.store.view.composite_updater import DailyUpdater, EntireUpdater, UpdateManager
from validol.model.store.view.view_flavors import ALL_VIEW_FLAVORS
from validol.model.resource_manager.resource_manager import ResourceManager
from validol.model.store.miners.prices import InvestingPrices
from validol.model.store.structures.atom import Atoms
from validol.model.store.structures.pattern import Patterns, StrPattern
from validol.model.store.structures.table import Tables
from validol.model.store.structures.pdf_helper import PdfHelpers
from validol.model.store.structures.scheduler import Schedulers
from validol.model.store.miners.daily_reports.expirations import Expirations
from validol.model.store.collectors.ml import MlCurve
from validol.model.store.structures.db_version import DbVersionManager
from validol.migration.migrate import migrate, init_version


class ModelLauncher:
    def __init__(self, controller_launcher):
        self.controller_launcher = controller_launcher

    def init_user(self, user_db):
        self.user_engine = create_engine('sqlite:///{}'.format(user_db))
        self.user_dbh = sqlite3.connect(user_db)

        self.resource_manager = ResourceManager(self)

        return self

    def init_data(self, main_dbh="main.db", user_db='user.db', proxy_cfg='proxy.cfg'):
        data_exists = os.path.exists("data")

        if not data_exists:
            os.makedirs("data")

        os.chdir("data")

        main_dbh_exists = os.path.isfile(main_dbh)

        self.init_user(user_db)

        self.main_dbh = sqlite3.connect(main_dbh)

        self.cache_engine = create_engine('sqlite:///cache.sqlite')

        if data_exists:
            migrate(self)
        else:
            self.write_db_version(init_version(self))

        if not main_dbh_exists:
            self.init_main_dbh()

        self.configure_proxy(proxy_cfg)

        return self

    def configure_proxy(self, proxy_cfg):
        if os.path.exists(proxy_cfg):
            with open(proxy_cfg, 'r') as infile:
                config = json.load(infile)

            socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, addr=config['ip'], port=config['port'],
                                  username=config['username'], password=config['password'])
            socket.socket = socks.socksocket

            print('Proxy configured')

    def init_main_dbh(self):
        real_conn = self.main_dbh

        self.main_dbh = sqlite3.connect(":memory:")

        self.update_weekly()

        real_conn.executescript("".join(self.main_dbh.iterdump()))

        self.main_dbh = real_conn

    def update(self, cls):
        return cls(self).update_entire()

    def update_daily(self):
        return self.update(DailyUpdater)

    def update_weekly(self):
        return self.update(EntireUpdater)

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

    def prepare_tables(self, table_pattern, actives_info):
        return self.resource_manager.prepare_tables(table_pattern, actives_info)

    def write_pdf_helper(self, ai, info, other_info):
        PdfHelpers(self).write_helper(ai, info, other_info)

    def read_pdf_helper(self, ai):
        return PdfHelpers(self).read_by_name(ai)

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

    def remove_expirations(self, ai):
        Expirations(self).remove_active(ai)

    def remove_ml(self, ai):
        MlCurve(self, ai).drop()

    def read_schedulers(self):
        return Schedulers(self).read()

    def write_scheduler(self, name, cron, working):
        Schedulers(self).write_scheduler(name, cron, working)

    def remove_scheduler(self, scheduler):
        Schedulers(self).remove_scheduler(scheduler)

    def switch_scheduler(self, scheduler):
        Schedulers(self).switch(scheduler)

    def get_update_manager(self):
        return UpdateManager(self)

    def get_db_version(self):
        return DbVersionManager(self).get_version()

    def write_db_version(self, version):
        DbVersionManager(self).write_version(version)

    def set_scheduler_next_time(self, scheduler, next_time):
        Schedulers(self).set_next_time(scheduler, next_time)

    def register_update(self, source):
        self.controller_launcher.register_update(source)

    def get_expiration_names(self):
        return Expirations(self).get_expirations()

    def get_expirations(self, ai):
        return Expirations(self).exp_info(ai)
