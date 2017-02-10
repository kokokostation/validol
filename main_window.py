from PyQt5 import QtGui, QtCore
import data_parser
import tables
import downloader
import table_dialog
import graph_dialog
import user_structures
from pyparsing import alphas
import startup
import interface_common

__all__ = ["Window", "draw_pattern"]

class Window(QtGui.QWidget):
    def __init__(self, app):
        QtGui.QWidget.__init__(self)

        self.app = app

        self.setWindowTitle("COTs")

        self.searchResult = None

        self.actives = QtGui.QListWidget()
        self.actives.itemDoubleClicked.connect(self.submit_active)
        self.searchLine = QtGui.QLineEdit()
        self.searchLine.setPlaceholderText("Search")
        self.searchLine.textChanged.connect(self.search)
        self.searchLine.returnPressed.connect(self.search)
        self.activesListLayout = QtGui.QVBoxLayout()
        self.activesListLayout.addWidget(self.searchLine)
        self.activesListLayout.addWidget(self.actives)

        self.platforms = QtGui.QListWidget()
        self.platforms.currentItemChanged.connect(self.platform_chosen)

        for code, name in data_parser.get_platforms():
            wi = QtGui.QListWidgetItem(name)
            wi.setToolTip(code)
            self.platforms.addItem(wi)

        self.platforms.setCurrentRow(0)

        self.drawTable = QtGui.QPushButton('Draw table')
        self.drawTable.clicked.connect(self.draw_table)

        self.clear = QtGui.QPushButton('Clear all')
        self.clear.clicked.connect(self.clear_actives)

        self.createTable = QtGui.QPushButton('Create table')
        self.createTable.clicked.connect(self.create_table)

        self.updateButton = QtGui.QPushButton('Update')
        self.updateButton.clicked.connect(self.on_update)

        self.removeTable = QtGui.QPushButton('Remove table')
        self.removeTable.clicked.connect(self.remove_table)

        self.leftLayout = QtGui.QVBoxLayout()
        self.leftLayout.addWidget(self.platforms)
        self.leftLayout.addWidget(self.updateButton)

        self.cached_prices = QtGui.QListWidget()
        self.set_cached_prices()

        self.tablesList = QtGui.QListWidget()
        self.availableTables = []
        self.set_tables()
        self.tablesList.itemDoubleClicked.connect(self.table_chosen)

        self.tableView = QtGui.QTextEdit()
        self.tableView.setReadOnly(True)

        self.main_layout = QtGui.QVBoxLayout(self)

        self.lists_layout = QtGui.QHBoxLayout()

        self.rightLayout = QtGui.QVBoxLayout()
        self.rightLayout.addWidget(self.cached_prices)
        self.rightLayout.addWidget(self.tablesList)
        self.rightLayout.addWidget(self.removeTable)
        self.rightLayout.addWidget(self.tableView)
        self.rightLayout.addWidget(self.createTable)

        self.actives_layout = QtGui.QVBoxLayout()
        self.actives_layout.addWidget(self.clear)
        self.actives_layout_widgets = []
        self.actives_layout_lines = []
        self.chosen_actives = []

        self.lists_layout.insertLayout(0, self.leftLayout)
        self.lists_layout.insertLayout(1, self.activesListLayout)
        self.lists_layout.addWidget(interface_common.scrollable_area(self.actives_layout))
        self.lists_layout.insertLayout(3, self.rightLayout)

        self.main_layout.insertLayout(0, self.lists_layout)
        self.main_layout.addWidget(self.drawTable)

        self.tables = []
        self.graphs = []
        self.tableDialogs = []

        self.showMaximized()

    def remove_table(self):
        user_structures.remove_table(self.tablesList.currentItem().text())
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
            self.searchResult = [searchText, self.actives.findItems(self.searchLine.text(), QtCore.Qt.MatchContains), 0]

        _, items, index = self.searchResult
        if items:
            self.actives.setCurrentItem(items[index % len(items)])
            self.searchResult[2] += 1

    def table_chosen(self):
        name, presentation, _ = self.availableTables[self.tablesList.currentRow()]
        self.tableView.setText(name + ":\n" + presentation)

    def set_tables(self):
        self.tablesList.clear()
        self.availableTables = []

        tables = user_structures.get_tables()
        for name, presentation, tablePattern in tables:
            wi = QtGui.QListWidgetItem(name)
            self.availableTables.append((name, presentation, tablePattern))
            self.tablesList.addItem(wi)

        self.tablesList.setCurrentRow(self.tablesList.count() - 1)

    def set_cached_prices(self):
        for url, name in data_parser.get_cached_prices():
            wi = QtGui.QListWidgetItem(name)
            wi.setToolTip(url)
            self.cached_prices.addItem(wi)

    def submit_active(self):
        self.chosen_actives.append((self.platforms.currentItem().toolTip(), self.platforms.currentItem().text(), self.actives.currentItem().text()))

        self.actives_layout_widgets.append((QtGui.QLineEdit(), QtGui.QLineEdit(), QtGui.QPushButton('Submit cached'), QtGui.QPushButton('Clear')))
        last_line_widgets = self.actives_layout_widgets[-1]

        self.actives_layout_lines.append(QtGui.QVBoxLayout())
        last_line = self.actives_layout_lines[-1]

        last_line_widgets[0].setReadOnly(True)
        last_line_widgets[0].setText(self.platforms.currentItem().text() + "/" + self.actives.currentItem().text())

        last_line_widgets[2].clicked.connect(lambda: self.submit_cached(last_line_widgets[1], self.cached_prices))
        last_line_widgets[3].clicked.connect(lambda: self.clearActive(last_line))

        for w in last_line_widgets:
            last_line.addWidget(w)

        self.actives_layout.insertLayout(len(self.actives_layout_lines), last_line)

    def submit_cached(self, lineEdit, listWidget):
        lineEdit.setText(listWidget.currentItem().toolTip())

    def platform_chosen(self):
        self.actives.clear()

        for active in data_parser.get_actives(self.platforms.currentItem().toolTip()):
            self.actives.addItem(active)

    def clearActive(self, vbox):
        i = self.actives_layout_lines.index(vbox)
        self.removeLine(i)

    def removeLine(self, i):
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
            self.removeLine(i)

    def add_price(self, new, url, name):
        if new:
            wi = QtGui.QListWidgetItem(name)
            wi.setToolTip(url)
            self.cached_prices.addItem(wi)

    def draw_table(self):
        tableName = self.tablesList.currentItem().text()
        _, tableLabels, tablePattern = self.availableTables[self.tablesList.currentRow()]
        tableLabels = [table.split(",") for table in tableLabels.split("\n")]
        info = []
        title = ""
        for i in range(len(self.actives_layout_widgets)):
            url, name = self.actives_layout_widgets[i][1].text(), None
            chosen_platform, chosen_platform_name, chosen_active = self.chosen_actives[i]
            if url:
                pair_id, name, new = downloader.get_active_info(downloader.normalize_url(url))
                self.add_price(new, url, name)
            else:
                pair_id = None

            title += alphas[i] + ": " + data_parser.title(chosen_platform_name, chosen_active, name) + "\n"
            info.append((chosen_platform, chosen_active, pair_id))

        dates, values = data_parser.prepare_tables(tablePattern, info)

        for i in range(len(tableLabels)):
            self.tables.append(tables.Table(dates, values[i], tableLabels[i], title))

        self.graphs.append(graph_dialog.GraphDialog(dates, values, tableName, tableLabels, title))

    def create_table(self):
        self.tableDialogs.append(table_dialog.TableDialog(lambda: self.set_tables()))

    def on_update(self):
        self.updateButton.setText("Wait a sec. Updating the data...")
        self.app.processEvents()
        if not startup.update():
            msg = QtGui.QMessageBox()
            msg.setIcon(QtGui.QMessageBox.Critical)
            msg.setText("Unable to update due to network error")
            msg.setWindowTitle("Network error")
            msg.exec_()
        self.updateButton.setText("Update")