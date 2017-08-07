import sys

from PyQt5 import QtCore, QtWidgets
from market_graphs.view.graph.graphs import CheckedGraph
from market_graphs.view.menu.graph_dialog import GraphDialog
from market_graphs.view.menu.main_window import Window
from market_graphs.view.menu.table_dialog import TableDialog
from market_graphs.view.table.tables import Table
from market_graphs.view.view_element import ViewElement


class ViewLauncher(ViewElement):
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
            Table(self.main_window, QtCore.Qt.Window, df, labels, title_info))

    def show_graph_dialog(self, df, table_pattern, title_info):
        self.graph_dialogs.append(
            GraphDialog(
                self.main_window, QtCore.Qt.Window, df, table_pattern, title_info,
                self.controller_launcher, self.model_launcher))

    def show_graph(self, df, pattern, table_labels, title):
        self.graphs.append(
            CheckedGraph(self.main_window, QtCore.Qt.Window, df, pattern, table_labels, title))

    def refresh_tables(self):
        self.main_window.tipped_list.refresh()

    def show_table_dialog(self):
        self.table_dialogs.append(
            TableDialog(self.main_window, QtCore.Qt.Window, self.controller_launcher,
                        self.model_launcher))
