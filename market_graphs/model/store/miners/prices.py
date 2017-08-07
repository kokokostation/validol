import datetime as dt
import re

import pandas as pd
import requests
from market_graphs.model.mine.downloader import read_url_text
from market_graphs.model.store.resource import Resource
from market_graphs.model.store.structures.structure import Structure, Base
from sqlalchemy import Column, String
from sqlalchemy.sql import select


def normalize_url(url):
    return re.sub(r'https://[^.]*\.', r'https://www.', url)


class InvestingPriceInfo(Base):
    __tablename__ = 'prices'
    pair_id = Column(String, primary_key=True)
    name = Column(String)
    url = Column(String)

    def __init__(self, pair_id, name, url):
        self.pair_id = pair_id
        self.name = name
        self.url = url


class InvestingPrices(Structure):
    def __init__(self, model_launcher):
        Structure.__init__(self, InvestingPriceInfo, model_launcher)

    def get_info_through_url(self, url):
        url = normalize_url(url)

        response = self.session.query(InvestingPriceInfo.pair_id, InvestingPriceInfo.name)\
            .filter(InvestingPriceInfo.url == url).first()

        if response:
            return response
        else:
            try:
                content = read_url_text(url)
            except requests.exceptions.ConnectionError:
                return [None] * 2

            pair_id = re.search(r'data-pair-id="(\d*)"', content).group(1)
            name = re.search(r'<title>(.*)</title>', content).group(1).rsplit(" - ")[0]

            self.write(InvestingPriceInfo(pair_id, name, url))

        return pair_id, name

    def get_prices(self):
        return pd.DataFrame(r.__dict__ for r in self.read())


class InvestingPrice(Resource):
    SCHEMA = [("Quot", "REAL")]
    INDEPENDENT = False

    def __init__(self, model_launcher, pair_id):
        Resource.__init__(self, model_launcher.main_dbh, "pair_id_{pair_id}".format(pair_id=pair_id),
                          InvestingPrice.SCHEMA)

        self.pair_id = pair_id

    def update(self):
        raise NotImplementedError

    def fill(self, first, last):
        start_date = first.strftime("%d/%m/%Y")
        end_date = last.strftime("%d/%m/%Y")

        session = requests.Session()

        response = session.post(
            url='https://ru.investing.com/instruments/HistoricalDataAjax',
            data={
                'action': 'historical_data',
                'curr_id': self.pair_id,
                'st_date': start_date,
                'end_date': end_date,
                'interval_sec': 'Daily'
            },
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'User-Agent': 'Mozilla/5.0'
            }
        )

        df = pd.DataFrame()

        df["Date"] = [dt.datetime.strptime(date, "%d.%m.%Y").date()
                        for date in re.findall(
                r'class="first left bold noWrap">(.*)</td>', response.text)]

        raw_prices = re.findall(
            r'<td.*class="(green|red)Font">(\d+(\.\d*)*(,\d*))</td>',
            response.text)

        df["Quot"] = [row[1].replace(".", "").replace(",", ".") for row in raw_prices]

        return df

    def read_dates(self, begin, end):
        first, last = self.range()

        try:
            if not first:
                self.write_df(self.fill(begin, end))
            else:
                if begin < first:
                    self.write_df(self.fill(begin, first - dt.timedelta(days=1)))
                if last < end:
                    self.write_df(self.fill(last + dt.timedelta(days=1), end))
        except requests.exceptions.ConnectionError:
            pass

        return Resource.read_dates(self, begin, end)

