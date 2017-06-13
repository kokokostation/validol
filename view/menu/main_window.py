from PyQt5 import QtWidgets, QtCore, QtWidgets

from model.store import user_structures, data_parser
from view import utils
from view.view_element import ViewElement


class Window(ViewElement, QtWidgets.QWidget):
    def __init__(self, app, controller_launcher):
        QtWidgets.QWidget.__init__(self)
        ViewElement.__init__(self, controller_launcher)

        self.app = app

        self.setWindowTitle("COTs")

        self.searchResult = None

        self.actives = QtWidgets.QListWidget()
        self.actives.itemDoubleClicked.connect(self.submit_active)
        self.searchLine = QtWidgets.QLineEdit()
        self.searchLine.setPlaceholderText("Search")
        self.searchLine.textChanged.connect(self.search)
        self.searchLine.returnPressed.connect(self.search)
        self.activesListLayout = QtWidgets.QVBoxLayout()
        self.activesListLayout.addWidget(self.searchLine)
        self.activesListLayout.addWidget(self.actives)

        self.platforms = QtWidgets.QListWidget()
        self.platforms.currentItemChanged.connect(self.platform_chosen)

        for code, name in data_parser.get_platforms():
            wi = QtWidgets.QListWidgetItem(name)
            wi.setToolTip(code)
            self.platforms.addItem(wi)

        self.platforms.setCurrentRow(0)

        self.drawTable = QtWidgets.QPushButton('Draw table')
        self.drawTable.clicked.connect(self.draw_table)

        self.clear = QtWidgets.QPushButton('Clear all')
        self.clear.clicked.connect(self.clear_actives)

        self.createTable = QtWidgets.QPushButton('Create table')
        self.createTable.clicked.connect(self.create_table)

        self.updateButton = QtWidgets.QPushButton('Update')
        self.updateButton.clicked.connect(self.on_update)

        self.removeTable = QtWidgets.QPushButton('Remove table')
        self.removeTable.clicked.connect(self.remove_table)

        self.leftLayout = QtWidgets.QVBoxLayout()
        self.leftLayout.addWidget(self.platforms)
        self.leftLayout.addWidget(self.updateButton)

        self.cached_prices = QtWidgets.QListWidget()
        self.set_cached_prices()

        self.tables_list = QtWidgets.QListWidget()
        self.available_tables = []
        self.set_tables()
        self.tables_list.itemDoubleClicked.connect(self.table_chosen)

        self.tableView = QtWidgets.QTextEdit()
        self.tableView.setReadOnly(True)

        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.lists_layout = QtWidgets.QHBoxLayout()

        self.rightLayout = QtWidgets.QVBoxLayout()
        self.rightLayout.addWidget(self.cached_prices)
        self.rightLayout.addWidget(self.tables_list)
        self.rightLayout.addWidget(self.removeTable)
        self.rightLayout.addWidget(self.tableView)
        self.rightLayout.addWidget(self.createTable)

        self.actives_layout = QtWidgets.QVBoxLayout()
        self.actives_layout.addWidget(self.clear)
        self.actives_layout_widgets = []
        self.actives_layout_lines = []
        self.chosen_actives = []

        self.lists_layout.insertLayout(0, self.leftLayout)
        self.lists_layout.insertLayout(1, self.activesListLayout)
        self.lists_layout.addWidget(
            utils.scrollable_area(self.actives_layout))
        self.lists_layout.insertLayout(3, self.rightLayout)

        self.main_layout.insertLayout(0, self.lists_layout)
        self.main_layout.addWidget(self.drawTable)

        self.tables = []
        self.graphs = []
        self.tableDialogs = []

        self.showMaximized()

    def remove_table(self):
        user_structures.remove_table(self.tables_list.currentItem().text())
        self.set_tables()

    def closeEvent(self, _):
        for graph in self.graphs:
            graph.close()

        for table in self.tables:
            table.close()

        for tableDialog in self.tableDialogs:
            tableDialog.close()

    def search(self):
        searchText = self.searchLine.text()
        if (self.searchResult and self.searchResult[0] != searchText) or not self.searchResult:
            self.searchResult = [searchText, self.actives.findItems(
                self.searchLine.text(), QtCore.Qt.MatchContains), 0]

        _, items, index = self.searchResult
        if items:
            self.actives.setCurrentItem(items[index % len(items)])
            self.searchResult[2] += 1

    def table_chosen(self):
        name, presentation, _ = self.available_tables[self.tables_list.currentRow()]
        self.tableView.setText(name + ":\n" + "\n".join(",".join(line) for line in presentation))

    def set_tables(self):
        self.tables_list.clear()
        self.available_tables = user_structures.get_tables()

        for name, presentation, tablePattern in self.available_tables:
            wi = QtWidgets.QListWidgetItem(name)
            self.tables_list.addItem(wi)

        self.tables_list.setCurrentRow(self.tables_list.count() - 1)

    def set_cached_prices(self):
        self.cached_prices.clear()

        for url, name in self.controller_launcher.get_cached_prices():
            wi = QtWidgets.QListWidgetItem(name)
            wi.setToolTip(url)
            self.cached_prices.addItem(wi)

    def submit_active(self):
        self.chosen_actives.append((self.platforms.currentItem().toolTip(),
                                    self.platforms.currentItem().text(),
                                    self.actives.currentItem().text()))

        self.actives_layout_widgets.append((QtWidgets.QLineEdit(),
                                            QtWidgets.QLineEdit(),
                                            QtWidgets.QPushButton('Submit cached'),
                                            QtWidgets.QPushButton('Clear')))
        last_line_widgets = self.actives_layout_widgets[-1]

        self.actives_layout_lines.append(QtWidgets.QVBoxLayout())
        last_line = self.actives_layout_lines[-1]

        last_line_widgets[0].setReadOnly(True)
        last_line_widgets[0].setText(
            self.platforms.currentItem().text() + "/" + self.actives.currentItem().text())

        last_line_widgets[2].clicked.connect(
            lambda: self.submit_cached(last_line_widgets[1], self.cached_prices))
        last_line_widgets[3].clicked.connect(
            lambda: self.clear_active(last_line))

        for w in last_line_widgets:
            last_line.addWidget(w)

        self.actives_layout.insertLayout(
            len(self.actives_layout_lines), last_line)

    def submit_cached(self, lineEdit, listWidget):
        lineEdit.setText(listWidget.currentItem().toolTip())

    def platform_chosen(self):
        self.actives.clear()

        for active in data_parser.get_actives(self.platforms.currentItem().toolTip()):
            self.actives.addItem(active)

    def clear_active(self, vbox):
        i = self.actives_layout_lines.index(vbox)
        self.remove_line(i)

    def remove_line(self, i):
        line = self.actives_layout_lines[i]

        for w in self.actives_layout_widgets[i]:
            line.removeWidget(w)
            w.hide()

        self.actives_layout.removeItem(line)

        self.actives_layout_lines.pop(i)
        self.actives_layout_widgets.pop(i)
        self.chosen_actives.pop(i)

    def clear_actives(self):
        for i in range(len(self.actives_layout_lines) - 1, -1, -1):
            self.remove_line(i)

    def draw_table(self):
        table_name, table_labels, table_pattern = self.available_tables[self.tables_list.currentRow()]
        actives = [(active[0], active[2], self.actives_layout_widgets[i][1].text())
                   for i, active in enumerate(self.chosen_actives)]
        self.controller_launcher.draw_table(table_name, table_labels, table_pattern, actives)

    def create_table(self):
        self.controller_launcher.show_table_dialog()

    def on_update(self):
        self.updateButton.setText("Wait a sec. Updating the data...")
        self.app.processEvents()
        if not self.controller_launcher.update_data():
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Unable to update due to network error")
            msg.setWindowTitle("Network error")
            msg.exec_()
        self.updateButton.setText("Update")
