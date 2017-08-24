import sys
from PyQt5 import QtCore, QtWidgets

from validol.view.graph.graphs import CheckedGraph
from validol.view.menu.graph_dialog import GraphDialog
from validol.view.menu.main_window import Window
from validol.view.menu.table_dialog import TableDialog
from validol.view.table.tables import Table
from validol.view.view_element import ViewElement
from validol.view.menu.pdf_helper_dialog import PdfHelperDialog
from validol.view.menu.glued_active_dialog import GluedActiveDialog
from validol.view.menu.pattern_edit_dialog import PatternEditDialog


class ViewLauncher(ViewElement):
    FLAGS = QtCore.Qt.Window

    def __init__(self, controller_launcher, model_launcher):
        ViewElement.__init__(self, controller_launcher, model_launcher)

        self.tables = []
        self.graph_dialogs = []
        self.graphs = []
        self.table_dialogs = []

    def show_main_window(self):
        app = QtWidgets.QApplication(sys.argv)
        self.main_window = Window(app, self.controller_launcher, self.model_launcher)
        sys.exit(app.exec_())

    def refresh_prices(self):
        self.main_window.set_cached_prices()

    def show_table(self, df, labels, title_info):
        self.tables.append(
            Table(ViewLauncher.FLAGS, df, labels, title_info))

    def show_graph_dialog(self, df, table_pattern, title_info):
        self.graph_dialogs.append(
            GraphDialog(
                ViewLauncher.FLAGS, df, table_pattern, title_info,
                self.controller_launcher, self.model_launcher))

    def show_graph(self, df, pattern, table_labels, title):
        self.graphs.append(
            CheckedGraph(ViewLauncher.FLAGS, df, pattern, table_labels, title))

    def refresh_tables(self):
        self.main_window.tipped_list.refresh()

    def show_table_dialog(self):
        self.table_dialogs.append(
            TableDialog(ViewLauncher.FLAGS, self.controller_launcher,
                        self.model_launcher))

    def show_pdf_helper_dialog(self, processors, widgets):
        return PdfHelperDialog(processors, widgets).get_data()

    def refresh_actives(self):
        self.main_window.platform_chosen()

    def get_chosen_actives(self):
        return self.main_window.chosen_actives

    def ask_name(self):
        return GluedActiveDialog().get_data()

    def edit_pattern(self, json_str):
        return PatternEditDialog(json_str).get_data()

    def on_close(self):
        for win in sum([self.tables, self.graphs, self.graph_dialogs, self.table_dialogs], []):
            win.close()
