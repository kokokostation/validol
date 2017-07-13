from datetime import date
from io import StringIO

import pandas as pd

from model.mine.downloader import read_url_one_filed_zip
from model.store.resource import Resource, Table
from model.utils import group_by


class Cots:
    CODE_ACTIVE_NAME = ["CFTC Market Code in Initials", "Market and Exchange Names"]
    CSV_NAMES = {
        "As of Date in Form YYYY-MM-DD": "Date",
        "Open Interest (All)": "OI",
        "Noncommercial Positions-Long (All)": "NCL",
        "Noncommercial Positions-Short (All)": "NCS",
        "Commercial Positions-Long (All)": "CL",
        "Commercial Positions-Short (All)": "CS",
        "Nonreportable Positions-Long (All)": "NRL",
        "Nonreportable Positions-Short (All)": "NRS",
        "Concentration-Net LT =4 TDR-Long (All)": "4L%",
        "Concentration-Net LT =4 TDR-Short (All)": "4S%",
        "Concentration-Net LT =8 TDR-Long (All)": "8L%",
        "Concentration-Net LT =8 TDR-Short (All)": "8S%"}

    def __init__(self, dbh):
        self.dbh = dbh

    def get_active_platform_name(self, market_and_exchange_names):
        return market_and_exchange_names.rsplit(" - ", 1)

    def update(self):
        platforms_table = Platforms(self.dbh)

        sources = ["http://www.cftc.gov/files/dea/history/deacot{curr_year}.zip"
            .format(curr_year=date.today().year)]

        if platforms_table.read().empty:
            sources.append("http://www.cftc.gov/files/dea/history/deacot1986_{prev_year}.zip"
                           .format(prev_year=date.today().year - 1))

        cols = Cots.CODE_ACTIVE_NAME + list(Cots.CSV_NAMES.keys())
        df = pd.DataFrame()

        for source in sources:
            df = df.append(pd.read_csv(
                StringIO(read_url_one_filed_zip(source.format(curr_year=date.today().year))),
                usecols=cols,
                parse_dates=["As of Date in Form YYYY-MM-DD"])[cols])

        df = df.rename(str, Cots.CSV_NAMES)
        df["CFTC Market Code in Initials"] = df.apply(lambda row:
                                                      row["CFTC Market Code in Initials"].strip(),
                                                      axis=1)

        info = group_by(df, Cots.CODE_ACTIVE_NAME)

        actives_table = Actives(self.dbh)

        platforms = set()
        actives = set()

        for code, name in info.groups.keys():
            active_name, platform_name = self.get_active_platform_name(name)
            platforms.add((code, platform_name))
            actives.add((code, active_name))

        for table, columns, values in (
                (platforms_table, ("PlatformCode", "PlatformName"), platforms),
                (actives_table, ("PlatformCode", "ActiveName"), actives)):
            table.write(pd.DataFrame(list(values), columns=columns))

        for code, name in info.groups.keys():
            active_name, _ = self.get_active_platform_name(name)
            Active(self.dbh, code, active_name, info.get_group((code, name))).update()


class Platforms(Table):
    def __init__(self, dbh):
        Table.__init__(self, dbh, "Platforms", [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("PlatformCode", "TEXT"),
            ("PlatformName", "TEXT")],
            "UNIQUE (PlatformCode) ON CONFLICT IGNORE")

    def get_platforms(self):
        return self.read().drop("id", axis=1)

    def get_platform_id(self, platform_code):
        return self.dbh.cursor().execute('''
            SELECT 
                id 
            FROM 
                "{table}" 
            WHERE 
                PlatformCode = ?'''.format(table=self.table), (platform_code,)).fetchone()[0]


class Actives(Table):
    def __init__(self, dbh):
        Table.__init__(self, dbh, "Actives", [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("PlatformCode", "TEXT"),
            ("ActiveName", "TEXT")],
            "UNIQUE (PlatformCode, ActiveName) ON CONFLICT IGNORE")

    def get_actives(self, platform):
        return [a for (a,) in self.dbh.cursor().execute('''
            SELECT
                ActiveName
            FROM
                "{table}"
            WHERE
                PlatformCode = ?'''.format(table=self.table), (platform,)).fetchall()]

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
    SCHEMA = [
        ("OI", "INTEGER"),
        ("NCL", "INTEGER"),
        ("NCS", "INTEGER"),
        ("CL", "INTEGER"),
        ("CS", "INTEGER"),
        ("NRL", "INTEGER"),
        ("NRS", "INTEGER"),
        ("4L%", "REAL"),
        ("4S%", "REAL"),
        ("8L%", "REAL"),
        ("8S%", "REAL")]

    def __init__(self, dbh, platform_code, active_name, update_info=pd.DataFrame()):
        active_id = Actives(dbh).get_active_id(platform_code, active_name)
        platform_id = Platforms(dbh).get_platform_id(platform_code)

        Resource.__init__(
            self,
            dbh,
            "Active_platform_{platform_id}_active_{active_id}".format(
                platform_id=platform_id,
                active_id=active_id),
            Active.SCHEMA)

        self.update_info = update_info

    def initial_fill(self):
        return self.update_info

    def fill(self, first, last):
        return self.update_info[(first < self.update_info.Date) &
                                (self.update_info.Date <= last)]
