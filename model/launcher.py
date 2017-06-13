import sqlite3
import requests

from model.store.monetary import Monetary
from model.store.prices import InvestingPrice, InvestingPrices


class ModelLauncher:
    def __init__(self):
        self.dbh = sqlite3.connect("main.db")

    def get_mbase(self, requested_dates):
        return Monetary(self.dbh).get_dates(requested_dates)

    def update(self):
        try:
            for cls in (Monetary,):
                cls(self.dbh).update()
            return True
        except requests.exceptions.ConnectionError:
            return False

    def get_prices_info(self, url):
        return InvestingPrices(self.dbh).get_info_through_url(url)

    def get_prices(self, dates, pair_id):
        return InvestingPrice(self.dbh, pair_id).get_dates(dates)

    def get_cached_prices(self):
        return InvestingPrices(self.dbh).get_prices()