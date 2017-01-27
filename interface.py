from PyQt4 import QtGui
import parser
import tables
import graphs

class Window(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.grabber = parser.Grabber()

        self.platforms = QtGui.QListWidget(self)
        self.platforms.itemClicked.connect(self.platform_chosen)
        for code, name in self.grabber.get_platforms():
            wi = QtGui.QListWidgetItem(name)
            wi.setToolTip(code)
            self.platforms.addItem(wi)

        self.actives = QtGui.QListWidget(self)

        self.cached_prices = QtGui.QListWidget(self)
        for url, name in self.grabber.get_cached_prices():
            wi = QtGui.QListWidgetItem(name)
            wi.setToolTip(url)
            self.cached_prices.addItem(wi)


        self.submit_active_button = QtGui.QPushButton('Submit active', self)
        self.submit_active_button.clicked.connect(self.submit_active)

        self.clear = QtGui.QPushButton('Clear', self)
        self.clear.clicked.connect(self.clear_actives)

        self.draw_table1 = QtGui.QPushButton('Draw table 1', self)
        self.draw_table1.clicked.connect(self.table1)

        self.draw_table2 = QtGui.QPushButton('Draw table 2', self)

        self.main_layout = QtGui.QVBoxLayout(self)

        self.lists_layout = QtGui.QHBoxLayout()

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
        self.bottom_buttons_layout.addWidget(self.draw_table1)
        self.bottom_buttons_layout.addWidget(self.draw_table2)

        self.main_layout.insertLayout(0, self.lists_layout)
        self.main_layout.insertLayout(1, self.bottom_buttons_layout)

        self.tables = []
        self.wins = []
        self.graph_dialogs = []

        self.showMaximized()

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

    def table1(self):
        url_widget = self.actives_layout_widgets[0][1]
        chosen_platform, chosen_platform_name, chosen_active = self.chosen_actives[0]
        data, name, url, new = self.grabber.get_info(chosen_platform, chosen_active, parser.table1_from_fields, url_widget.text())
        if new:
            wi = QtGui.QListWidgetItem(name)
            wi.setToolTip(url)
            self.cached_prices.addItem(wi)

        title = chosen_platform_name + "/" + chosen_active + "; Price: " + name

        self.table = tables.draw_table(data, parser.table1_labels, title)
        self.win = graphs.draw_graph([(data, parser.graph1_info)], title)

class GraphDialog(QtGui.QWidget):
    def __init__(self, table_labels, window):
        QtGui.QWidget.__init__(self)

        self.main_layout = QtGui.QVBoxLayout(self)
        self.upper_layout = QtGui.QHBoxLayout(self)
        self.labels_layout = QtGui.QVBoxLayout(self)
        self.buttons_layout = QtGui.QHBoxLayout(self)

        self.main_layout.insertLayout(0, self.upper_layout)
        self.main_layout.insertLayout(1, self.buttons_layout)

        self.pattern_list = QtGui.QListWidget(self)


        self.upper_layout.insertLayout(0, self.labels_layout)
        self.upper_layout.addWidget()
