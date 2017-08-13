import sys

from PyQt5 import QtCore, QtWidgets
from validol.view.graph.graphs import CheckedGraph
from validol.view.menu.graph_dialog import GraphDialog
from validol.view.menu.main_window import Window
from validol.view.menu.table_dialog import TableDialog
from validol.view.table.tables import Table
from validol.view.view_element import ViewElement


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
            Table(self.main_window, ViewLauncher.FLAGS, df, labels, title_info))

    def show_graph_dialog(self, df, table_pattern, title_info):
        self.graph_dialogs.append(
            GraphDialog(
                self.main_window, ViewLauncher.FLAGS, df, table_pattern, title_info,
                self.controller_launcher, self.model_launcher))

    def show_graph(self, df, pattern, table_labels, title):
        self.graphs.append(
            CheckedGraph(self.main_window, ViewLauncher.FLAGS, df, pattern, table_labels, title))

    def refresh_tables(self):
        self.main_window.tipped_list.refresh()

    def show_table_dialog(self):
        self.table_dialogs.append(
            TableDialog(self.main_window, ViewLauncher.FLAGS, self.controller_launcher,
                        self.model_launcher))
