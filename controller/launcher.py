from itertools import chain

from pyparsing import alphas

from model.launcher import ModelLauncher
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
        title_info = []
        for i, (flavor, platform, active, price_url) in enumerate(actives):
            price_name, pair_id = [None] * 2
            if price_url:
                pair_id, price_name = self.model_launcher.get_prices_info(price_url)
                self.view_launcher.refresh_prices()

            info.append((flavor, platform, active, pair_id))
            title_info.append((flavor, platform, active, price_name))

        df = self.model_launcher.prepare_tables(table_pattern, info)

        for i, labels in enumerate(table_pattern.formula_groups):
            self.view_launcher.show_table(df, labels, title_info)

        self.view_launcher.show_graph_dialog(df, table_pattern, title_info)

    def draw_graph(self, df, pattern, table_labels, title):
        self.view_launcher.show_graph(df, pattern, table_labels, title)

    def refresh_tables(self):
        self.view_launcher.refresh_tables()

    def show_table_dialog(self):
        self.view_launcher.show_table_dialog()

