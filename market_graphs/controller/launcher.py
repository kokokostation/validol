from market_graphs.model.launcher import ModelLauncher
from market_graphs.view.launcher import ViewLauncher


class ControllerLauncher:
    def __init__(self):
        self.model_launcher = ModelLauncher().init_data()

        self.view_launcher = ViewLauncher(self, self.model_launcher)
        self.view_launcher.show_main_window()

    def update_data(self):
        return self.model_launcher.update()

    def draw_table(self, table_pattern, actives_info, prices_info):
        title_info = []
        for i, (active_info, price_url) in enumerate(zip(actives_info, prices_info)):
            price_name, pair_id = [None] * 2
            if price_url:
                pair_id, price_name = self.model_launcher.get_prices_info(price_url)
                self.view_launcher.refresh_prices()

            prices_info[i] = pair_id
            title_info.append(active_info + [price_name])

        df = self.model_launcher.prepare_tables(table_pattern, actives_info, prices_info)

        for i, labels in enumerate(table_pattern.formula_groups):
            self.view_launcher.show_table(df, labels, title_info)

        self.view_launcher.show_graph_dialog(df, table_pattern, title_info)

    def draw_graph(self, df, pattern, table_labels, title):
        self.view_launcher.show_graph(df, pattern, table_labels, title)

    def refresh_tables(self):
        self.view_launcher.refresh_tables()

    def show_table_dialog(self):
        self.view_launcher.show_table_dialog()

