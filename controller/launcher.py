import datetime as dt
import os

import requests
from pyparsing import alphas

from model import utils
from model.mine import downloader
from model.store import filenames, data_parser
from view.launcher import ViewLauncher
from model.launcher import ModelLauncher

from model.store.data_parser import get_active, get_actives
from itertools import groupby
from controller.evaluator import NumericStringParser
from model.store.user_structures import get_atoms

class ControllerLauncher:
    def __init__(self):
        self.init_fs() # to remove

        self.model_launcher = ModelLauncher()

        self.view_launcher = ViewLauncher(self)
        self.view_launcher.show_main_window()

    def init_fs(self):
        ifNeedsUpdate = False
        if not os.path.exists("data"):
            ifNeedsUpdate = True
            os.makedirs("data")

        os.chdir("data")

        if not os.path.exists("prices"):
            os.makedirs("prices")

        if ifNeedsUpdate:
            self.update_data()

    def update_data(self):
        return self.model_launcher.update()

    def update_data_(self): # to remove
        try:
            dates_file = open(filenames.datesFile, "a+")
            dates_file.seek(0)

            last_net_date = downloader.get_last_date()
            written_dates = dates_file.read().splitlines()

            if written_dates and utils.parse_isoformat_date(written_dates[-1]) == last_net_date:
                return True

            monetary_file = open(filenames.monetaryFile, "a+")
            monetary_file.seek(0)

            content = monetary_file.read()
            if content:
                last_date = content.splitlines()[-1].split(",")[0]
            else:
                last_date = ""
            monetary_file.write(
                downloader.get_net_mbase(last_date, dt.date.today().isoformat()))

            monetary_file.close()

            net_platforms = downloader.get_platforms()
            platforms_file = open(filenames.platformsFile, "w")
            for code, name in net_platforms:
                if not os.path.exists(code):
                    os.makedirs(code)
                    os.makedirs(os.path.join(code, filenames.parsed))
                platforms_file.write(code + " " + name + "\n")
            platforms_file.close()

            dates = downloader.get_dates(last_net_date)
            all_dates = downloader.get_net_dates()
            all_dates.append(last_net_date)
            all_dates.extend(dates)
            all_dates = sorted(list(set(all_dates)))

            for code, _ in net_platforms:
                index = data_parser.get_actives(code)
                for date in all_dates[len(written_dates):]:
                    filename = os.path.join(code, date.isoformat())
                    if os.path.isfile(filename):
                        continue

                    if date == all_dates[-1]:
                        data = downloader.get_current_actives(code)
                    else:
                        data = downloader.get_actives(date, code)

                    if data_parser.parse_date(code, date, data, index):
                        file = open(filename, "w")
                        file.write(data)
                        file.close()

            for date in all_dates[len(written_dates):]:
                dates_file.write(date.isoformat() + "\n")
            dates_file.close()

            return True
        except requests.exceptions.ConnectionError:
            return False

    def draw_table(self, table_name, table_labels, table_pattern, actives):
        info = []
        title = ""
        for i, (platform, active, price_url) in enumerate(actives):
            price_name, pair_id = [None] * 2
            if price_url:
                pair_id, price_name = self.model_launcher.get_prices_info(price_url)
                self.view_launcher.refresh_prices()

            title += alphas[i] + ": " + data_parser.title(platform, active, price_name) + "\n"
            info.append((platform, active, pair_id))

        dates, values = self.prepare_tables(table_pattern, info)

        for i, labels in enumerate(table_labels):
            self.view_launcher.show_table(dates, values[i], labels, title)

        self.view_launcher.show_graph_dialog(dates, values, table_name, table_labels, title)

    def draw_graph(self, dates, values, pattern, table_labels, title):
        self.view_launcher.show_graph(dates, values, pattern, table_labels, title)

    def refresh_tables(self):
        self.view_launcher.refresh_tables()

    def show_table_dialog(self):
        self.view_launcher.show_table_dialog()

    def prepare_active(self, platform, active, prices_pair_id):
        dates, values = get_active(platform, active, get_actives(platform))
        mbase = self.model_launcher.get_mbase(dates)

        if not prices_pair_id:
            prices = [None] * len(dates)
        else:
            prices = self.model_launcher.get_prices(dates, prices_pair_id)

        groupedMbase = [(mbase[0], 1)] + [(k, len(list(g)))
                                          for k, g in groupby(mbase)]
        deltas = []
        for i in range(1, len(groupedMbase)):
            k, n = groupedMbase[i]
            delta = k - groupedMbase[i - 1][0]

            for j in range(n):
                deltas.append(delta / n)

        for i in range(len(dates)):
            values[i].extend([prices[i], mbase[i], deltas[i]])

        return dates, values

    def prepare_tables(self, tablePattern, info):
        data = [self.prepare_active(platform, active, prices_pair_id)
                for platform, active, prices_pair_id in info]

        compiler = NumericStringParser()

        allAtoms = dict([(name, compiler.compile(formula))
                         for name, formula, _ in get_atoms()])

        allDates, indexes = utils.merge_lists([dates for dates, _ in data])
        newValues = []
        for table in tablePattern:
            values = [[None for _ in range(len(table))]
                      for _ in range(len(allDates))]
            for i in range(len(table)):
                atoms, formula = table[i]
                atoms = [(allAtoms[atom], active) for atom, active in atoms]
                func = compiler.compile(formula)
                if False not in [index < len(data) for _, index in atoms]:
                    intersection = utils.intersect_lists(
                        [indexes[index] for _, index in atoms])
                    for j in range(len(intersection)):
                        args = [atom(data[active][1][j]) for atom, active in atoms]
                        values[intersection[j]][i] = func(args)
            newValues.append(values)

        return allDates, newValues

    def get_cached_prices(self):
        return self.model_launcher.get_cached_prices()
