from validol.model.launcher import ModelLauncher
from validol.view.launcher import ViewLauncher


class ControllerLauncher:
    def __init__(self):
        self.model_launcher = ModelLauncher().init_data()

        self.view_launcher = ViewLauncher(self, self.model_launcher)
        self.view_launcher.show_main_window()

    def update_data(self, how):
        return self.model_launcher.update(how)

    def draw_table(self, table_pattern, actives_info, prices_info):
        title_info = []
        for i, (active_info, price_url) in enumerate(zip(actives_info, prices_info)):
            price_name, pair_id = [None] * 2
            if price_url:
                pair_id, price_name = self.model_launcher.get_prices_info(price_url)
                self.view_launcher.refresh_prices()

            prices_info[i] = pair_id
            title_info.append((active_info, price_name))

        df = self.model_launcher.prepare_tables(table_pattern, actives_info, prices_info)

        for i, labels in enumerate(table_pattern.formula_groups):
            self.view_launcher.show_table(df, labels, title_info)

        self.view_launcher.show_graph_dialog(df, table_pattern, title_info)

    def draw_graph(self, df, pattern, table_labels, title):
        self.view_launcher.show_graph(df, pattern, table_labels, title)

    def refresh_tables(self):
        self.view_launcher.refresh_tables()

    def refresh_actives(self):
        self.view_launcher.refresh_actives()

    def show_table_dialog(self):
        self.view_launcher.show_table_dialog()

    def show_pdf_helper_dialog(self, processors, widgets):
        return self.view_launcher.show_pdf_helper_dialog(processors, widgets)

    def get_chosen_actives(self):
        return self.view_launcher.get_chosen_actives()

    def ask_name(self):
        return self.view_launcher.ask_name()

    def edit_pattern(self, json_str):
        return self.view_launcher.edit_pattern(json_str)

    def main_window_closed(self):
        self.view_launcher.on_close()

