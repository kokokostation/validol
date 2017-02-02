from PyQt4 import QtGui, QtCore
import data_parser
import graphs
import utils
import interface_common
from functools import partial
from pyparsing import alphas
import itertools

class GraphDialog(QtGui.QWidget):
    def __init__(self, dates, values, tableName, tableLabels, title):
        QtGui.QWidget.__init__(self)

        self.setWindowTitle(tableName)

        self.dates = dates

        self.values = [list(itertools.chain.from_iterable([value[i] for value in values])) for i in range(len(dates))]
        self.title = title
        self.tableName = tableName
        self.tableLabels = utils.flatten(tableLabels)

        self.main_layout = QtGui.QVBoxLayout(self)
        self.upper_layout = QtGui.QHBoxLayout()
        self.buttons_layout = QtGui.QHBoxLayout()
        self.labels_layout = QtGui.QVBoxLayout()
        self.labels_submit_layout = QtGui.QVBoxLayout()
        self.patternChoiceLayout = QtGui.QVBoxLayout()

        interface_common.set_title(self.main_layout, title)

        self.main_layout.insertLayout(1, self.upper_layout, stretch=10)
        self.main_layout.insertLayout(2, self.buttons_layout)

        self.pattern_list = QtGui.QListWidget()
        self.patterns = data_parser.get_patterns()
        if tableName in self.patterns:
            for graphName in self.patterns[tableName].keys():
                self.pattern_list.addItem(graphName)
        self.pattern_list.itemDoubleClicked.connect(self.draw_item)

        self.patternTree = QtGui.QTreeWidget()

        self.patternChoiceLayout.addWidget(self.pattern_list)
        self.patternChoiceLayout.addWidget(self.patternTree)

        self.graphsTree = QtGui.QTreeWidget()

        self.patternTitle = QtGui.QLineEdit()
        self.patternTitle.setPlaceholderText("Pattern title")
        self.labels_submit_layout.addWidget(self.patternTitle)

        self.labels_submit_layout.addWidget(interface_common.scrollable_area(self.labels_layout))

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

        for i in range(len(self.tableLabels)):
            lastLabel = QtGui.QHBoxLayout()

            textBox = QtGui.QLineEdit()
            textBox.setReadOnly(True)
            textBox.setText(self.tableLabels[i])
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

    def closeEvent(self, _):
        for graph in self.graphs:
            graph.close()

    def draw_item(self, item):
        pattern = self.patterns[self.tableName][item.text()]
        self.patternTree.clear()
        interface_common.draw_pattern(self.patternTree, pattern, self.tableLabels)

    def indexChanged(self, comboBox, color):
        comboBox.setStyleSheet("color: white; background-color: " + graphs.qcolors[color])

    def draw_graph(self):
        self.graphs.append(graphs.CheckedGraph(self.dates, self.values,
                                               self.patterns[self.tableName][self.pattern_list.currentItem().text()],
                                               self.tableLabels, self.title))

    def submit_graph(self):
        places = []

        graph = [[[] for _ in range(3)] for _ in range(2)]
        for i in range(len(self.labels)):
            textBox, buttonGroups, checkBoxes, comboBox = self.labels[i]
            lr, t = buttonGroups[0].checked_button(), buttonGroups[1].checked_button()
            if lr and t:
                color = comboBox.currentText()
                toAppend = i
                if t[0] != 0:
                    if color in places:
                        toAppend = toAppend, places.index(color)
                    else:
                        toAppend = toAppend, len(places)
                        places.append(color)

                graph[lr[0]][t[0]].append(toAppend)

        self.currentPattern.append(graph)

        interface_common.add_root(self.graphsTree, self.currentPattern[-1], self.tableLabels, str(len(self.currentPattern)))

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

        data_parser.add_pattern(self.tableName, patternTitle, self.currentPattern)
        utils.add_to_dict(self.patterns, self.tableName, patternTitle, self.currentPattern)

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