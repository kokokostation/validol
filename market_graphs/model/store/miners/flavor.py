import datetime as dt
from io import StringIO

import pandas as pd
from market_graphs.model.store.resource import Resource, Table
from market_graphs.model.utils import group_by


class Flavor:
    def __init__(self, model_launcher):
        self.model_launcher = model_launcher

    @staticmethod
    def get_active_platform_name(market_and_exchange_names):
        return [name.strip() for name in market_and_exchange_names.rsplit("-", 1)]

    def if_initial(self, flavor):
        return Platforms(self.model_launcher, flavor).read_df().empty

    def get_df(self, flavor):
        cols = list(flavor["keys"].values()) + \
               list(flavor["values"].keys()) + \
               flavor.get("add_cols", [])

        df = pd.DataFrame()

        for csv in self.load_csvs(flavor):
            df = df.append(pd.read_csv(
                StringIO(csv),
                usecols=cols,
                parse_dates=[flavor["date"]],
                date_parser=lambda date: dt.datetime.strptime(date, flavor["date_fmt"]).date()))

        df = df.rename(str, flavor["values"])
        df[flavor["keys"]["platform_active"]] = df.apply(lambda row:
                                                         row[flavor["keys"]["platform_active"]]
                                                         .strip(), axis=1)

        return df

    def update_flavor(self, df, flavor):
        info = group_by(df, [flavor["keys"]["platform_code"],
                             flavor["keys"]["platform_active"]])

        actives_table = Actives(self.model_launcher, flavor)
        platforms_table = Platforms(self.model_launcher, flavor)

        platforms = set()
        actives = set()

        for code, name in info.groups.keys():
            active_name, platform_name = Flavor.get_active_platform_name(name)
            platforms.add((code, platform_name))
            actives.add((code, active_name))

        for table, columns, values in (
                (platforms_table, ("PlatformCode", "PlatformName"), platforms),
                (actives_table, ("PlatformCode", "ActiveName"), actives)):
            table.write_df(pd.DataFrame(list(values), columns=columns))

        for code, name in info.groups.keys():
            active_name, _ = Flavor.get_active_platform_name(name)
            Active(self.model_launcher, flavor, code, active_name, info.get_group((code, name))).update()

    def load_csvs(self, flavor):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError


class Platforms(Table):
    def __init__(self, model_launcher, flavor):
        Table.__init__(
            self,
            model_launcher.main_dbh,
            "Platforms_{flavor}".format(flavor=flavor["name"]), [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("PlatformCode", "TEXT"),
            ("PlatformName", "TEXT")],
            "UNIQUE (PlatformCode) ON CONFLICT IGNORE")

    def get_platforms(self):
        return self.read_df()

    def get_platform_id(self, platform_code):
        return self.dbh.cursor().execute('''
            SELECT 
                id 
            FROM 
                "{table}" 
            WHERE 
                PlatformCode = ?'''.format(table=self.table), (platform_code,)).fetchone()[0]


class Actives(Table):
    def __init__(self, model_launcher, flavor):
        Table.__init__(
            self,
            model_launcher.main_dbh,
            "Actives_{flavor}".format(flavor=flavor["name"]), [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("PlatformCode", "TEXT"),
            ("ActiveName", "TEXT")],
            "UNIQUE (PlatformCode, ActiveName) ON CONFLICT IGNORE")

    def get_actives(self, platform):
        return pd.read_sql('''
            SELECT
                ActiveName
            FROM
                "{table}"
            WHERE
                PlatformCode = "{code}"'''.format(table=self.table, code=platform), self.dbh)

    def get_active_id(self, platform_code, active_name):
        return self.dbh.cursor().execute('''
            SELECT 
                id 
            FROM 
                "{table}" 
            WHERE 
                PlatformCode = ? AND 
                ActiveName = ?'''.format(table=self.table),
            (platform_code, active_name)).fetchone()[0]


class Active(Resource):
    def __init__(self, model_launcher, flavor, platform_code, active_name, update_info=pd.DataFrame()):
        active_id = Actives(model_launcher, flavor).get_active_id(platform_code, active_name)
        platform_id = Platforms(model_launcher, flavor).get_platform_id(platform_code)

        Resource.__init__(
            self,
            model_launcher.main_dbh,
            "Active_platform_{platform_id}_active_{active_id}_{flavor}".format(
                platform_id=platform_id,
                active_id=active_id,
                flavor=flavor["name"]),
            flavor["schema"])

        self.update_info = update_info

    def initial_fill(self):
        return self.update_info

    def fill(self, first, last):
        return self.update_info[(first < self.update_info.Date) &
                                (self.update_info.Date <= last)]
