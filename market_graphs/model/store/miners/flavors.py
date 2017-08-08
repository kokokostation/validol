from collections import OrderedDict
from datetime import date

from market_graphs.model.mine.downloader import read_url_one_filed_zip, read_url_text
from market_graphs.model.store.miners.flavor import Flavor
from market_graphs.model.utils import group_by


def fix_atoms(df):
    df["CL"] = df["PMPL"] + df["SDPL"]
    df["CS"] = df["PMPS"] + df["SDPS"]
    df["NCL"] = df["MMPL"] + df["ORPL"]
    df["NCS"] = df["MMPS"] + df["ORPS"]


DISAGGREGATED_SCHEMA = [
    ("OI", "INTEGER"),
    ("NCL", "INTEGER"),
    ("NCS", "INTEGER"),
    ("CL", "INTEGER"),
    ("CS", "INTEGER"),
    ("NRL", "INTEGER"),
    ("NRS", "INTEGER"),
    ("PMPL", "INTEGER"),
    ("PMPS", "INTEGER"),
    ("SDPL", "INTEGER"),
    ("SDPS", "INTEGER"),
    ("MMPL", "INTEGER"),
    ("MMPS", "INTEGER"),
    ("ORPL", "INTEGER"),
    ("ORPS", "INTEGER"),
    ("4GL%", "REAL"),
    ("4GS%", "REAL"),
    ("8GL%", "REAL"),
    ("8GS%", "REAL"),
    ("4L%", "REAL"),
    ("4S%", "REAL"),
    ("8L%", "REAL"),
    ("8S%", "REAL"),
    ("SDPSpr", "INTEGER"),
    ("MMPSpr", "INTEGER"),
    ("ORPSpr", "INTEGER")
]

CFTC_DATE_FMT = "%Y-%m-%d"

CFTC_FUTURES_ONLY = {
    "keys": {
        "platform_code": "CFTC Market Code in Initials",
        "platform_active": "Market and Exchange Names"},
    "date": "As of Date in Form YYYY-MM-DD",
    "values": {
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
        "Concentration-Net LT =8 TDR-Short (All)": "8S%"},
    "schema": [
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
        ("8S%", "REAL")],
    "name": "cftc_futures_only",
    "initial_prefix": "http://www.cftc.gov/files/dea/history/deacot1986_",
    "year_prefix": "http://www.cftc.gov/files/dea/history/deacot",
    "disaggregated": False,
    "date_fmt": CFTC_DATE_FMT
}

def cftc_disaggregated(initial_prefix, year_prefix, name):
    return {
        "keys": {
            "platform_code": "CFTC_Market_Code",
            "platform_active": "Market_and_Exchange_Names"},
        "date": "Report_Date_as_YYYY-MM-DD",
        "values": {
            "Report_Date_as_YYYY-MM-DD": "Date",
            "Open_Interest_All": "OI",
            "Prod_Merc_Positions_Long_All": "PMPL",
            "Prod_Merc_Positions_Short_All": "PMPS",
            "Swap_Positions_Long_All": "SDPL",
            "Swap__Positions_Short_All": "SDPS",
            "M_Money_Positions_Long_All": "MMPL",
            "M_Money_Positions_Short_All": "MMPS",
            "Other_Rept_Positions_Long_All": "ORPL",
            "Other_Rept_Positions_Short_All": "ORPS",
            "NonRept_Positions_Long_All": "NRL",
            "NonRept_Positions_Short_All": "NRS",
            "Conc_Gross_LE_4_TDR_Long_All": "4GL%",
            "Conc_Gross_LE_4_TDR_Short_All": "4GS%",
            "Conc_Gross_LE_8_TDR_Long_All": "8GL%",
            "Conc_Gross_LE_8_TDR_Short_All": "8GS%",
            "Conc_Net_LE_4_TDR_Long_All": "4L%",
            "Conc_Net_LE_4_TDR_Short_All": "4S%",
            "Conc_Net_LE_8_TDR_Long_All": "8L%",
            "Conc_Net_LE_8_TDR_Short_All": "8S%",
            "Swap__Positions_Spread_All": "SDPSpr",
            "M_Money_Positions_Spread_All": "MMPSpr",
            "Other_Rept_Positions_Spread_All": "ORPSpr"
        },
        "schema": DISAGGREGATED_SCHEMA,
        "name": name,
        "initial_prefix": initial_prefix,
        "year_prefix": year_prefix,
        "disaggregated": True,
        "date_fmt": CFTC_DATE_FMT
    }

CFTC_DISAGGREGATED_FUTURES_ONLY = cftc_disaggregated(
    initial_prefix="http://www.cftc.gov/files/dea/history/fut_disagg_txt_hist_2006_",
    year_prefix="http://www.cftc.gov/files/dea/history/fut_disagg_txt_",
    name="cftc_disaggregated_futures_only")


CFTC_DISAGGREGATED_FUTURES_AND_OPTIONS_COMBINED = cftc_disaggregated(
    initial_prefix="http://www.cftc.gov/files/dea/history/com_disagg_txt_hist_2006_",
    year_prefix="http://www.cftc.gov/files/dea/history/com_disagg_txt_",
    name="cftc_disaggregated_futures_and_options_combined")


class Cftc(Flavor):
    FLAVORS = [
        CFTC_FUTURES_ONLY,
        CFTC_DISAGGREGATED_FUTURES_ONLY,
        CFTC_DISAGGREGATED_FUTURES_AND_OPTIONS_COMBINED]

    def __init__(self, model_launcher):
        Flavor.__init__(self, model_launcher)

    def load_csvs(self, flavor):
        sources = [(
            "{year_prefix}{curr_year}.zip"
                .format(year_prefix=flavor["year_prefix"],
                        curr_year=date.today().year),
            False)]

        if self.if_initial(flavor):
            sources.append((
                "{initial_prefix}{prev_year}.zip"
                    .format(initial_prefix=flavor["initial_prefix"],
                            prev_year=date.today().year - 1),
                True))

        return [read_url_one_filed_zip(source, cache_enabled) for source, cache_enabled in sources]

    def update(self):
        for flavor in Cftc.FLAVORS:
            df = self.get_df(flavor)
            if flavor["disaggregated"]:
                fix_atoms(df)

            self.update_flavor(df, flavor)


def ice(name, ice_flavor):
    return {
        "keys": {
            "platform_code": "CFTC_Market_Code",
            "platform_active": "Market_and_Exchange_Names"},
        "date": "As_of_Date_Form_MM/DD/YYYY",
        "values": {
            "As_of_Date_Form_MM/DD/YYYY": "Date",
            "Open_Interest_All": "OI",
            "Prod_Merc_Positions_Long_All": "PMPL",
            "Prod_Merc_Positions_Short_All": "PMPS",
            "Swap_Positions_Long_All": "SDPL",
            "Swap__Positions_Short_All": "SDPS",
            "M_Money_Positions_Long_All": "MMPL",
            "M_Money_Positions_Short_All": "MMPS",
            "Other_Rept_Positions_Long_All": "ORPL",
            "Other_Rept_Positions_Short_All": "ORPS",
            "NonRept_Positions_Long_All": "NRL",
            "NonRept_Positions_Short_All": "NRS",
            "Conc_Gross_LE_4_TDR_Long_All": "4GL%",
            "Conc_Gross_LE_4_TDR_Short_All": "4GS%",
            "Conc_Gross_LE_8_TDR_Long_All": "8GL%",
            "Conc_Gross_LE_8_TDR_Short_All": "8GS%",
            "Conc_Net_LE_4_TDR_Long_All": "4L%",
            "Conc_Net_LE_4_TDR_Short_All": "4S%",
            "Conc_Net_LE_8_TDR_Long_All": "8L%",
            "Conc_Net_LE_8_TDR_Short_All": "8S%",
            "Swap__Positions_Spread_All": "SDPSpr",
            "M_Money_Positions_Spread_All": "MMPSpr",
            "Other_Rept_Positions_Spread_All": "ORPSpr"
        },
        "schema": DISAGGREGATED_SCHEMA,
        "name": name,
        "ice_flavor": ice_flavor,
        "add_cols": ["FutOnly_or_Combined"],
        "date_fmt": "%m/%d/%Y"
    }

ICE_FUTURES_ONLY = ice("ice_futures_only", "FutOnly")
ICE_COMBINED = ice("ice_combined", "Combined")


class Ice(Flavor):
    FLAVORS = [
        ICE_FUTURES_ONLY,
        ICE_COMBINED]

    def __init__(self, model_launcher):
        Flavor.__init__(self, model_launcher)

    def load_csvs(self, flavor):
        if self.if_initial(flavor):
            years = range(2011, date.today().year + 1)
        else:
            years = [date.today().year]

        return [read_url_text("https://www.theice.com/publicdocs/futures/COTHist{year}.csv"
                              .format(year=year), year != years[-1]) for year in years]

    def update(self):
        df = self.get_df(Ice.FLAVORS[0])

        fix_atoms(df)

        grouped_df = group_by(df, ["FutOnly_or_Combined"])

        for flavor in Ice.FLAVORS:
            self.update_flavor(grouped_df.get_group(flavor["ice_flavor"]), flavor)

GLUED_ACTIVE = {"name": "glued_active"}

FLAVORS_MAP = OrderedDict((flavor["name"], flavor)
                          for flavor in sum([exchange.FLAVORS for exchange in (Cftc, Ice)],
                                            [GLUED_ACTIVE]))