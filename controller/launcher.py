from itertools import chain

from pyparsing import alphas

from model.launcher import ModelLauncher
from model.utils import flatten
from view.launcher import ViewLauncher


class ControllerLauncher:
    def __init__(self):
        self.model_launcher = ModelLauncher()

        self.view_launcher = ViewLauncher(self, self.model_launcher)
        self.view_launcher.show_main_window()

    def update_data(self):
        return self.model_launcher.update()

    def draw_table(self, table_pattern, actives):
        info = []
        title = ""
        for i, (platform, active, price_url) in enumerate(actives):
            price_name, pair_id = [None] * 2
            if price_url:
                pair_id, price_name = self.model_launcher.get_prices_info(price_url)
                self.view_launcher.refresh_prices()

            active_title = "{}/{}".format(platform, active) # interface details?
            if price_name:
                active_title += "; Quot from: {}".format(price_name)

            title += "{}: {}\n".format(alphas[i], active_title)
            info.append((platform, active, pair_id))

        dates, values = self.model_launcher.prepare_tables(table_pattern, info)

        for i, labels in enumerate(table_pattern.atom_groups):
            self.view_launcher.show_table(dates, values[i], labels, title)

        flattened_values = [list(chain.from_iterable([value[i] for value in values]))
                            for i in range(len(dates))]
        self.view_launcher.show_graph_dialog(
            dates,
            flattened_values,
            table_pattern.name,
            flatten(table_pattern.atom_groups),
            title)

    def draw_graph(self, dates, values, pattern, table_labels, title):
        self.view_launcher.show_graph(dates, values, pattern, table_labels, title)

    def refresh_tables(self):
        self.view_launcher.refresh_tables()

    def show_table_dialog(self):
        self.view_launcher.show_table_dialog()

