from datetime import date

from validol.model.mine.downloader import read_url_one_filed_zip, read_url_text
from validol.model.store.miners.weekly_reports.flavor import Flavor
from validol.model.utils.utils import group_by, flatten
from validol.model.store.miners.daily_reports.moex import MOEX


def fix_atoms(df):
    df = df.copy()

    df["CL"] = df["PMPL"] + df["SDPL"]
    df["CS"] = df["PMPS"] + df["SDPS"]
    df["NCL"] = df["MMPL"] + df["ORPL"]
    df["NCS"] = df["MMPS"] + df["ORPS"]

    return df


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
    "keys": ["CFTC Market Code in Initials", "Market and Exchange Names"],
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
        "keys": ["CFTC_Market_Code", "Market_and_Exchange_Names"],
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


def cftc_financial_futures(initial_prefix, year_prefix, name):
    return {
        "keys": ["CFTC_Market_Code", "Market_and_Exchange_Names"],
        "date": "Report_Date_as_YYYY-MM-DD",
        "values": {
            "Report_Date_as_YYYY-MM-DD": "Date",
            "Open_Interest_All": "OI",
            "Dealer_Positions_Long_All": "DIPL",
            "Dealer_Positions_Short_All": "DIPS",
            "Dealer_Positions_Spread_All": "DIPSpr",
            "Asset_Mgr_Positions_Long_All": "AMPL",
            "Asset_Mgr_Positions_Short_All": "AMPS",
            "Asset_Mgr_Positions_Spread_All": "AMPSpr",
            "Lev_Money_Positions_Long_All": "LMPL",
            "Lev_Money_Positions_Short_All": "LMPS",
            "Lev_Money_Positions_Spread_All": "LMPSpr",
            "Other_Rept_Positions_Long_All": "ORPL",
            "Other_Rept_Positions_Short_All": "ORPS",
            "Other_Rept_Positions_Spread_All": "ORPSpr",
            "NonRept_Positions_Long_All": "NRL",
            "NonRept_Positions_Short_All": "NRS"
        },
        "schema": [
            ("OI", "INTEGER"),
            ("DIPL", "INTEGER"),
            ("DIPS", "INTEGER"),
            ("DIPSpr", "INTEGER"),
            ("AMPL", "INTEGER"),
            ("AMPS", "INTEGER"),
            ("AMPSpr", "INTEGER"),
            ("LMPL", "INTEGER"),
            ("LMPS", "INTEGER"),
            ("LMPSpr", "INTEGER"),
            ("ORPL", "INTEGER"),
            ("ORPS", "INTEGER"),
            ("ORPSpr", "INTEGER"),
            ("NRL", "INTEGER"),
            ("NRS", "INTEGER")
        ],
        "name": name,
        "initial_prefix": initial_prefix,
        "year_prefix": year_prefix,
        "disaggregated": False,
        "initial_date_fmt": "%m/%d/%Y 12:00:00 AM",
        "date_fmt": CFTC_DATE_FMT
    }


CFTC_FINANCIAL_FUTURES_FUTURES_ONLY = cftc_financial_futures(
    initial_prefix="http://www.cftc.gov/files/dea/history/fin_fut_txt_2006_",
    year_prefix="http://www.cftc.gov/files/dea/history/fut_fin_txt_",
    name='cftc_financial_futures_futures_only'
)


CFTC_FINANCIAL_FUTURES_COMBINED = cftc_financial_futures(
    initial_prefix="http://www.cftc.gov/files/dea/history/fin_com_txt_2006_",
    year_prefix="http://www.cftc.gov/files/dea/history/com_fin_txt_",
    name='cftc_financial_futures_combined'
)


class Cftc(Flavor):
    FLAVORS = [
        CFTC_FUTURES_ONLY,
        CFTC_DISAGGREGATED_FUTURES_ONLY,
        CFTC_DISAGGREGATED_FUTURES_AND_OPTIONS_COMBINED,
        CFTC_FINANCIAL_FUTURES_FUTURES_ONLY,
        CFTC_FINANCIAL_FUTURES_COMBINED
    ]

    LAST_YEAR = 2016

    def __init__(self, model_launcher):
        Flavor.__init__(self, model_launcher, Cftc.FLAVORS)

    def load_csvs(self, flavor):
        curr_year = date.today().year

        if self.if_initial(flavor):
            sources = [(
                "{initial_prefix}{prev_year}.zip"
                    .format(initial_prefix=flavor["initial_prefix"],
                            prev_year=Cftc.LAST_YEAR),
                True,
                flavor.get("initial_date_fmt", flavor['date_fmt']))]

            begin = Cftc.LAST_YEAR + 1
        else:
            sources = []
            begin = self.flavor_latest_year(flavor)

        sources += [(
            "{year_prefix}{year}.zip"
                .format(year_prefix=flavor["year_prefix"],
                        year=year),
            year != curr_year,
            flavor['date_fmt']
        ) for year in range(begin, curr_year + 1)]

        result = []
        for source, cache_enabled, date_fmt in sources:
            content = read_url_one_filed_zip(source, cache_enabled)
            if content is not None:
                result.append((content, date_fmt))

        return result

    def update_flavor(self, flavor):
        df = self.get_df(flavor)

        if flavor["disaggregated"]:
            df = fix_atoms(df)

        return self.process_flavor(df, flavor)


def ice(name, ice_flavor):
    return {
        "keys": ["CFTC_Market_Code", "Market_and_Exchange_Names"],
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
        Flavor.__init__(self, model_launcher, Ice.FLAVORS)

        self.grouped_df = None

    def load_csvs(self, flavor):
        if self.if_initial(flavor):
            begin = 2011
        else:
            begin = self.flavor_latest_year(flavor)

        result = []
        curr_year = date.today().year
        for year in range(begin, curr_year + 1):
            content = read_url_text("https://www.theice.com/publicdocs/futures/COTHist{year}.csv"
                                    .format(year=year), year != curr_year)
            if content is not None:
                result.append((content, flavor['date_fmt']))

        return result

    def prepare_update(self):
        df = self.get_df(Ice.FLAVORS[0])

        df = fix_atoms(df)

        self.grouped_df = group_by(df, ["FutOnly_or_Combined"])

    def update_flavor(self, flavor):
        if self.grouped_df is None:
            self.prepare_update()

        return self.process_flavor(self.grouped_df.get_group(flavor["ice_flavor"]), flavor)


WEEKLY_REPORT_FLAVORS = flatten([exchange.FLAVORS for exchange in (Cftc, Ice)]) + [MOEX]