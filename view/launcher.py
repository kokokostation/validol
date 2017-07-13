import sys

from PyQt5 import QtCore, QtWidgets

from view.graph.graphs import CheckedGraph
from view.menu.graph_dialog import GraphDialog
from view.menu.main_window import Window
from view.menu.table_dialog import TableDialog
from view.table.tables import Table
from view.view_element import ViewElement


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

    def show_table(self, dates, values, labels, title):
        self.tables.append(
            Table(self.main_window, QtCore.Qt.Window,
                  dates, values, labels, title))

    def show_graph_dialog(self, dates, values, table_name, table_labels, title):
        self.graph_dialogs.append(
            GraphDialog(
                self.main_window, QtCore.Qt.Window, dates,
                values, table_name, table_labels, title,
                self.controller_launcher, self.model_launcher))

    def show_graph(self, dates, values, pattern, table_labels, title):
        self.graphs.append(
            CheckedGraph(self.main_window, QtCore.Qt.Window, dates,
                         values, pattern, table_labels, title))

    def refresh_tables(self):
        self.main_window.set_tables()

    def show_table_dialog(self):
        self.table_dialogs.append(
            TableDialog(self.main_window, QtCore.Qt.Window, self.controller_launcher,
                        self.model_launcher))
