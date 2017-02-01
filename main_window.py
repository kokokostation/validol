from PyQt5 import QtGui
import data_parser
import tables
import downloader
import table_dialog
import graph_dialog
import formulae
from pyparsing import alphas

__all__ = ["Window", "draw_pattern"]

class Window(QtGui.QWidget):
    def __init__(self, app):
        QtGui.QWidget.__init__(self)

        self.app = app

        self.setWindowTitle("COTs")

        self.platforms = QtGui.QListWidget()
        self.platforms.currentItemChanged.connect(self.platform_chosen)
        for code, name in data_parser.get_platforms():
            wi = QtGui.QListWidgetItem(name)
            wi.setToolTip(code)
            self.platforms.addItem(wi)

        self.actives = QtGui.QListWidget()

        self.cached_prices = QtGui.QListWidget()
        self.set_cached_prices()

        self.submit_active_button = QtGui.QPushButton('Submit active')
        self.submit_active_button.clicked.connect(self.submit_active)

        self.clear = QtGui.QPushButton('Clear')
        self.clear.clicked.connect(self.clear_actives)

        self.drawTable = QtGui.QPushButton('Draw table')
        self.drawTableable.clicked.connect(self.draw_table)

        self.createTable = QtGui.QPushButton('Create table')
        self.createTable.clicked.connect(self.create_table)

        self.updateButton = QtGui.QPushButton('Update')
        self.updateButton.clicked.connect(self.on_update)

        self.tablesList = QtGui.QListWidget()
        self.availableTables = {}
        self.set_tables()
        self.tablesList.currentItemChanged.connect(self.table_chosen)

        self.tableView = QtGui.QTextEdit()
        self.tableView.setReadOnly(True)

        self.main_layout = QtGui.QVBoxLayout(self)

        self.lists_layout = QtGui.QHBoxLayout()

        self.rightLayout = QtGui.QVBoxLayout()
        self.rightLayout.addWidget(self.cached_prices)
        self.rightLayout.addWidget(self.tablesList)
        self.rightLayout.addWidget(self.tableView)
        self.rightLayout.addWidget(self.createTable)

        self.actives_layout = QtGui.QVBoxLayout()
        self.actives_layout.addWidget(self.clear)
        self.actives_layout_widgets = []
        self.actives_layout_lines = []
        self.chosen_actives = []

        self.bottom_buttons_layout = QtGui.QHBoxLayout()

        self.lists_layout.addWidget(self.platforms)
        self.lists_layout.addWidget(self.actives)
        self.lists_layout.insertLayout(2, self.actives_layout)
        self.lists_layout.addWidget(self.cached_prices)

        self.bottom_buttons_layout.addWidget(self.submit_active_button)
        self.bottom_buttons_layout.addWidget(self.drawTable)
        self.bottom_buttons_layout.addWidget(self.updateButton)

        self.main_layout.insertLayout(0, self.lists_layout)
        self.main_layout.insertLayout(1, self.bottom_buttons_layout)

        self.tables = []
        self.graphs = []

        self.showMaximized()

    def table_chosen(self):
        self.tableView.setText(self.availableTables[self.tablesList.currentItem()])

    def set_tables(self):
        self.tablesList.clear()
        self.availableTables = {}

        tables = formulae.get_tables()
        for name, table in tables:
            wi = QtGui.QListWidgetItem(name)
            self.availableTables[wi] = table
            self.tablesList.addItem(wi)

    def set_cached_prices(self):
        for url, name in data_parser.get_cached_prices():
            wi = QtGui.QListWidgetItem(name)
            wi.setToolTip(url)
            self.cached_prices.addItem(wi)

    def submit_active(self):
        if len(self.chosen_actives) == 4:
            return

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

        self.actives_layout.insertLayout(len(self.actives_layout_lines) - 1, last_line)

    def submit_cached(self, lineEdit, listWidget):
        lineEdit.setText(listWidget.currentItem().toolTip())

    def platform_chosen(self):
        self.actives.clear()

        for active in self.grabber.get_actives(self.platforms.currentItem().toolTip()):
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
        tlci = self.tablesList.currentItem()
        tableName, tablePattern = tlci.text(), self.availableTables[tlci]
        info = []
        title = ""
        for i in range(len(self.actives_layout_widgets)):
            url = self.actives_layout_widgets[i][1].text()
            chosen_platform, chosen_platform_name, chosen_active = self.chosen_actives[i]
            url, name, new = downloader.get_active_info(downloader.normalize_url(url))
            self.add_price(new, url, name)

            title += alphas[i] + ": " + data_parser.title(chosen_platform_name, chosen_active, name) + "\n"
            info.append((chosen_platform, chosen_active, url))

        dates, values = data_parser.prepare_tables(tables, info)

        for i in range(len(tablePattern)):
            self.tables.append(tables.draw_table(dates, values[i], tablePattern[i], title))

        self.graphs.append(graph_dialog.GraphDialog(dates, values, tableName, tablePattern, title))

    def create_table(self):
        self.tableDialog = table_dialog.TableDialog()

    def on_update(self):
        self.updateButton.setText("Wait a sec. Updating the data...")
        self.app.processEvents()
        downloader.update()
        self.updateButton.setText("Update")