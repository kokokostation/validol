from PyQt5 import QtGui, QtCore
import data_parser
import tables
import graphs
import utils
import trees
import downloader
from bisect import bisect_left
import datetime as dt
from functools import partial

__all__ = ["Window", "draw_pattern"]

class Window(QtGui.QWidget):
    def __init__(self, app):
        QtGui.QWidget.__init__(self)

        self.grabber = data_parser.Grabber()

        self.app = app

        self.setWindowTitle("COTs")

        self.platforms = QtGui.QListWidget()
        self.platforms.itemClicked.connect(self.platform_chosen)
        for code, name in data_parser.get_platforms():
            wi = QtGui.QListWidgetItem(name)
            wi.setToolTip(code)
            self.platforms.addItem(wi)

        self.actives = QtGui.QListWidget()

        self.cached_prices = QtGui.QListWidget()
        for url, name in data_parser.get_cached_prices():
            wi = QtGui.QListWidgetItem(name)
            wi.setToolTip(url)
            self.cached_prices.addItem(wi)


        self.submit_active_button = QtGui.QPushButton('Submit active')
        self.submit_active_button.clicked.connect(self.submit_active)

        self.clear = QtGui.QPushButton('Clear')
        self.clear.clicked.connect(self.clear_actives)

        self.draw_table1 = QtGui.QPushButton('Draw table 1')
        self.draw_table1.clicked.connect(self.table1)

        self.draw_table2 = QtGui.QPushButton('Draw table 2')
        self.draw_table2.clicked.connect(self.table2)

        self.updateButton = QtGui.QPushButton('Update')
        self.updateButton.clicked.connect(self.on_update)

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
        self.bottom_buttons_layout.addWidget(self.updateButton)

        self.main_layout.insertLayout(0, self.lists_layout)
        self.main_layout.insertLayout(1, self.bottom_buttons_layout)

        self.tables = []
        self.graphs = []

        self.showMaximized()

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

    def table1(self):
        table = "table 1"
        url_widget = self.actives_layout_widgets[0][1]
        chosen_platform, chosen_platform_name, chosen_active = self.chosen_actives[0]
        data, name, url, new = self.grabber.consolidate(chosen_platform, chosen_active, url_widget.text())
        self.add_price(new, url, name)

        title = data_parser.title(chosen_platform_name, chosen_active, name)

        self.tables.append(tables.draw_table(data, data_parser.table1_labels, data_parser.table1_key_types, title))
        self.graphs.append(GraphDialog(table, data_parser.table1_labels[1:], data, title, self.grabber))

    def table2(self):
        actives = "ABCD"
        table = "table 2"
        denotions = []
        info = []
        titles = []
        for i in range(len(self.chosen_actives)):
            url = self.actives_layout_widgets[i][1].text()
            chosen_platform, chosen_platform_name, chosen_active = self.chosen_actives[i]
            info.append(self.grabber.consolidate(chosen_platform, chosen_active, url))
            data, name, url, new = info[-1]
            titles.append(data_parser.title(chosen_platform_name, chosen_active, name))
            title = actives[i] + ": " + titles[-1]
            denotions.append(title)
            self.tables.append(tables.draw_table(data, data_parser.table2_labels, data_parser.table2_key_types, title))
            self.add_price(new, url, name)

        labels = []
        primary_labels = data_parser.table2_labels[1:]
        primary_labels.extend(["ALN", "ASN"])
        allDates = sorted(list(set([d["Date"] for data, _, _, _ in info for d in data])))
        allData = [{"Date": date} for date in allDates]
        for i in range(len(info)):
            for label in primary_labels:
                labels.append(label + " " + actives[i])
            for data in info[i][0]:
                j = bisect_left(allDates, data["Date"])
                for label in primary_labels:
                    if label in data:
                        allData[j][label + " " + actives[i]] = data[label]

        ratios = [(0, 1), (2, 0), (3, 0)]
        tempLabels = []
        for a, b in ratios:
            if max(a, b) < len(info):
                labelA, labelB = "Quot " + actives[a], "Quot " + actives[b]
                labels.append(labelA + "/" + labelB)
                tempLabels.append((labelA, labelB))

        for data in allData:
            for labelA, labelB in tempLabels:
                if labelA in data and labelB in data and data[labelB] != 0:
                    data[labelA + "/" + labelB] = data[labelA] / data[labelB]

        self.tables.append(tables.draw_table(allData, ["Date"] + labels[-len(tempLabels):], [dt.date] + ([float] * len(tempLabels)), "Quots ratios"))
        self.graphs.append(GraphDialog(table, labels, allData, "\n".join(denotions), self.grabber))

    def on_update(self):
        self.updateButton.setText("Wait a sec. Updating the data...")
        self.app.processEvents()
        downloader.update()
        self.updateButton.setText("Update")

class GraphDialog(QtGui.QWidget):
    def __init__(self, tableName, tableLabels, data, title, grabber):
        QtGui.QWidget.__init__(self)

        self.setWindowTitle(title)

        self.data = data
        self.title = title
        self.grabber = grabber
        self.tableName = tableName

        self.main_layout = QtGui.QVBoxLayout(self)
        self.upper_layout = QtGui.QHBoxLayout()
        self.buttons_layout = QtGui.QHBoxLayout()
        self.labels_layout = QtGui.QVBoxLayout()
        self.labels_submit_layout = QtGui.QVBoxLayout()
        self.patternChoiceLayout = QtGui.QVBoxLayout()

        if "\n" in title:
            denotions = QtGui.QTextEdit()
            denotions.setText(title)
            denotions.setReadOnly(True)
            self.main_layout.addWidget(denotions, stretch=1)

        self.main_layout.insertLayout(1, self.upper_layout, stretch=10)
        self.main_layout.insertLayout(2, self.buttons_layout)

        self.pattern_list = QtGui.QListWidget()
        if tableName in grabber.patterns:
            for graphName in grabber.patterns[tableName].keys():
                self.pattern_list.addItem(graphName)
        self.pattern_list.itemDoubleClicked.connect(self.draw_item)

        self.patternTree = QtGui.QTreeWidget()

        self.patternChoiceLayout.addWidget(self.pattern_list)
        self.patternChoiceLayout.addWidget(self.patternTree)

        self.graphsTree = QtGui.QTreeWidget()

        self.patternTitle = QtGui.QLineEdit()
        self.patternTitle.setPlaceholderText("Pattern title")
        self.labels_submit_layout.addWidget(self.patternTitle)

        self.scrollForLabels = QtGui.QScrollArea()
        self.scrollForLabels.setWidgetResizable(True)
        self.inner = QtGui.QFrame(self.scrollForLabels)
        self.inner.setLayout(self.labels_layout)
        self.scrollForLabels.setWidget(self.inner)
        self.labels_submit_layout.addWidget(self.scrollForLabels)

        self.upper_layout.insertLayout(0, self.labels_submit_layout)
        self.upper_layout.addWidget(self.graphsTree)
        self.upper_layout.insertLayout(2, self.patternChoiceLayout)

        self.submitPattern = QtGui.QPushButton('Submit pattern')
        self.submitPattern.clicked.connect(self.submit_pattern)

        self.drawGraph = QtGui.QPushButton('Draw graph')
        self.drawGraph.clicked.connect(self.draw_graph)

        self.buttons_layout.addWidget(self.submitPattern)
        self.buttons_layout.addWidget(self.drawGraph)

        self.graphs = []

        self.labels = []

        for i in range(len(tableLabels)):
            lastLabel = QtGui.QHBoxLayout()

            textBox = QtGui.QLineEdit()
            textBox.setReadOnly(True)
            textBox.setText(tableLabels[i])
            lastLabel.addWidget(textBox)

            checkBoxes = [QtGui.QCheckBox(label) for label in ["left", "right", "line", "bar", "-bar"]]

            buttonGroups = []
            for t in [[0, 1], [2, 3, 4]]:
                buttonGroups.append(MyButtonGroup())
                for j in t:
                    buttonGroups[-1].add_item(checkBoxes[j])
                    lastLabel.addWidget(checkBoxes[j])

            comboBox = QtGui.QComboBox()
            model = comboBox.model()
            for color in graphs.qcolors:
                item = QtGui.QStandardItem(color)
                item.setBackground(QtGui.QColor(color))
                model.appendRow(item)

            comboBox.setStyleSheet("color: white; background-color: " + graphs.qcolors[0])
            comboBox.currentIndexChanged.connect(partial(self.indexChanged, comboBox))

            lastLabel.addWidget(comboBox)

            self.labels.append((textBox, buttonGroups, checkBoxes, comboBox))

            self.labels_layout.insertLayout(i, lastLabel)

        self.submitGraph = QtGui.QPushButton('Submit graph')
        self.submitGraph.clicked.connect(self.submit_graph)
        self.labels_submit_layout.addWidget(self.submitGraph)

        self.currentPattern = []

        self.showMaximized()

    def draw_item(self, item):
        pattern = self.grabber.patterns[self.tableName][item.text()]
        self.patternTree.clear()
        trees.draw_pattern(self.patternTree, pattern)

    def indexChanged(self, comboBox, color):
        comboBox.setStyleSheet("color: white; background-color: " + graphs.qcolors[color])

    def draw_graph(self):
        self.graphs.append(graphs.CheckedGraph(self.data, self.grabber.patterns[self.tableName][self.pattern_list.currentItem().text()], self.title))

    def submit_graph(self):
        places = []

        graph = [[[] for _ in range(3)] for _ in range(2)]
        for textBox, buttonGroups, checkBoxes, comboBox in self.labels:
            lr, t = buttonGroups[0].checked_button(), buttonGroups[1].checked_button()
            if lr and t:
                color = comboBox.currentText()
                toAppend = textBox.text()
                if t[0] != 0:
                    if color in places:
                        toAppend = textBox.text(), places.index(color)
                    else:
                        toAppend = textBox.text(), len(places)
                        places.append(color)

                graph[lr[0]][t[0]].append(toAppend)

        self.currentPattern.append(graph)

        trees.add_root(self.graphsTree, self.currentPattern[-1], str(len(self.currentPattern)))

        self.clear_comboboxes()
        self.clear_checkboxes()

    def clear_checkboxes(self):
        for _, _, checkBoxes, _ in self.labels:
            for cb in checkBoxes:
                cb.setChecked(False)

    def clear_comboboxes(self):
        for _, _, _, comboBox in self.labels:
            comboBox.setCurrentIndex(0)

    def submit_pattern(self):
        patternTitle = self.patternTitle.text()
        if not patternTitle:
            return

        self.pattern_list.addItem(patternTitle)

        utils.add_to_dict(self.grabber.patterns, self.tableName, patternTitle, self.currentPattern)

        data_parser.add_pattern(self.tableName, patternTitle, self.currentPattern)

        self.clear_checkboxes()
        self.clear_comboboxes()
        self.patternTitle.clear()

        self.graphsTree.clear()
        self.currentPattern = []

class MyButtonGroup():
    def __init__(self):
        self.buttons = []
        self.last = None

    def add_item(self, button):
        button.stateChanged.connect(lambda: self.state_changed(button))
        self.buttons.append(button)

    def id(self, button):
        return self.buttons.index(button)

    def state_changed(self, button):
        if self.last and self.last != button:
            self.last.setChecked(False)

        self.last = button

    def checked_button(self):
        if self.last and self.last.checkState() == QtCore.Qt.Checked:
            return self.buttons.index(self.last), self.last.text()