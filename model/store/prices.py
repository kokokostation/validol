from model.store.resource import Resource, Table
import requests
import datetime as dt
import re
import pandas as pd
from model.mine.downloader import read_url_text


def normalize_url(url):
    return re.sub(r'https://[^.]*\.', r'https://www.', url)


class InvestingPrices(Table):
    def __init__(self, dbh):
        Table.__init__(self, dbh, "Prices",
                       [("pair_id", "TEXT PRIMARY KEY"), ("Name", "TEXT"), ("URL", "TEXT")])

    def get_info_through_url(self, url):
        url = normalize_url(url)

        c = self.dbh.cursor()
        c.execute("""
            SELECT
                pair_id, name
            FROM 
                {table}
            WHERE
                URL = ?""".format(table=self.table), (url,))
        response = c.fetchone()

        if response:
            return response
        else:
            try:
                content = read_url_text(url)
            except requests.exceptions.ConnectionError:
                return [None] * 2

            pair_id = re.search(r'data-pair-id="(\d*)"', content).group(1)
            name = re.search(r'<title>(.*)</title>', content).group(1).rsplit(" - ")[0]

            self.dbh.cursor().execute("""
                INSERT OR IGNORE INTO
                    {table}
                VALUES ({qs})""".format(table=self.table,
                                        qs=",".join("?" * len(self.schema))),
                (pair_id, name, url))

        return pair_id, name

    def get_prices(self):
        return self.dbh.cursor().execute(
            "SELECT URL, Name FROM {table}".format(table=self.table)).fetchall()


class InvestingPrice(Resource):
    def __init__(self, dbh, pair_id):
        Resource.__init__(
            self,
            dbh,
            "pair_id_{pair_id}".format(pair_id=pair_id),
            [("Price", "REAL")])

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

        df["Price"] = [row[1].replace(".", "").replace(",", ".") for row in raw_prices]

        return df

    def get_dates(self, requested_dates):
        first, last = self.range()

        try:
            if not first:
                self.write(self.fill(requested_dates[0], requested_dates[-1]))
            else:
                if requested_dates[0] < first:
                    self.write(self.fill(requested_dates[0], first - dt.timedelta(days=1)))
                if last < requested_dates[-1]:
                    self.write(self.fill(last + dt.timedelta(days=1), requested_dates[-1]))
        except requests.exceptions.ConnectionError:
            pass

        dates = self.read(
            ["Price"],
            requested_dates[0],
            requested_dates[-1])

        dates = dates.set_index("Date").to_dict()['Price']

        return [dates.get(date, None) for date in requested_dates]

