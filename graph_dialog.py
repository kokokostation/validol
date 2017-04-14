from PyQt5 import QtGui, QtCore
import data_parser
import graphs
import utils
import interface_common
from functools import partial
from pyparsing import alphas
import itertools
import user_structures


class GraphDialog(QtGui.QWidget):

    def __init__(self, dates, values, tableName, tableLabels, title):
        QtGui.QWidget.__init__(self)

        self.setWindowTitle(tableName)

        self.dates = dates

        self.values = [list(itertools.chain.from_iterable(
            [value[i] for value in values])) for i in range(len(dates))]
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
        patterns = user_structures.get_patterns()
        self.patterns = {}
        for patternTableName, graphName, pattern in patterns:
            if patternTableName == tableName:
                self.pattern_list.addItem(graphName)
                self.patterns[graphName] = pattern

        if self.pattern_list.count() > 0:
            self.pattern_list.setCurrentRow(0)

        self.pattern_list.itemDoubleClicked.connect(self.draw_item)

        self.patternTree = QtGui.QTreeWidget()

        self.removePattern = QtGui.QPushButton('Remove pattern')
        self.removePattern.clicked.connect(self.remove_pattern)

        self.patternChoiceLayout.addWidget(self.pattern_list)
        self.patternChoiceLayout.addWidget(self.removePattern)
        self.patternChoiceLayout.addWidget(self.patternTree)

        self.graphsTree = QtGui.QTreeWidget()

        self.patternTitle = QtGui.QLineEdit()
        self.patternTitle.setPlaceholderText("Pattern title")
        self.labels_submit_layout.addWidget(self.patternTitle)

        self.labels_submit_layout.addWidget(
            interface_common.scrollable_area(self.labels_layout))

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

        for i, label in enumerate(self.tableLabels):
            lastLabel = QtGui.QHBoxLayout()

            textBox = QtGui.QLineEdit()
            textBox.setReadOnly(True)
            textBox.setText(label)
            lastLabel.addWidget(textBox)

            checkBoxes = [
                QtGui.QCheckBox(label) for label in ["left", "right", "line", "bar", "-bar"]]

            buttonGroups = []
            for t in [[0, 1], [2, 3, 4]]:
                buttonGroups.append(interface_common.MyButtonGroup())
                for j in t:
                    buttonGroups[-1].add_item(checkBoxes[j])
                    lastLabel.addWidget(checkBoxes[j])

            comboBoxes = [QtGui.QComboBox() for _ in range(2)]
            for comboBox in comboBoxes:
                model = comboBox.model()
                for color in graphs.colors:
                    item = QtGui.QStandardItem("")
                    item.setBackground(QtGui.QColor(*color))
                    model.appendRow(item)

                comboBox.currentIndexChanged.connect(
                    partial(self.indexChanged, comboBox))
                comboBox.highlighted.connect(partial(self.activated, comboBox))
                self.indexChanged(comboBox, 0)

                lastLabel.addWidget(comboBox)

            self.labels.append((textBox, buttonGroups, checkBoxes, comboBoxes))

            self.labels_layout.insertLayout(i, lastLabel)

        self.submitGraph = QtGui.QPushButton('Submit graph')
        self.submitGraph.clicked.connect(self.submit_graph)
        self.labels_submit_layout.addWidget(self.submitGraph)

        self.currentPattern = []

        self.showMaximized()

    def remove_pattern(self):
        title = self.pattern_list.currentItem().text()
        self.pattern_list.takeItem(self.pattern_list.currentRow())
        self.patternTree.clear()
        self.patternTree.setHeaderLabel("")
        del self.patterns[title]
        user_structures.remove_pattern(self.tableName, title)

    def closeEvent(self, _):
        for graph in self.graphs:
            graph.close()

    def draw_item(self, item):
        pattern = self.patterns[item.text()]
        self.patternTree.clear()
        interface_common.draw_pattern(
            self.patternTree, pattern, self.tableLabels)
        self.patternTree.setHeaderLabel(item.text())

    def activated(self, comboBox, _=None):
        comboBox.setStyleSheet("color: white; background-color: transparent")

    def indexChanged(self, comboBox, color):
        comboBox.setStyleSheet(
            "color: white; background-color: rgb" + str(graphs.colors[color]))

    def draw_graph(self):
        self.graphs.append(graphs.CheckedGraph(self.dates, self.values,
                                               self.patterns[
                                                   self.pattern_list.currentItem().text()],
                                               self.tableLabels, self.title))

    def submit_graph(self):
        places = []

        graph = [[[] for _ in range(3)] for _ in range(2)]
        for i, label in enumerate(self.labels):
            textBox, buttonGroups, checkBoxes, comboBoxes = label
            lr, t = buttonGroups[
                0].checked_button(), buttonGroups[1].checked_button()
            if lr and t:
                color = comboBoxes[0].currentIndex()
                toAppend = [i]
                if t[0] != 0:
                    if color in places:
                        toAppend.append(places.index(color))
                    else:
                        toAppend.append(len(places))
                        places.append(color)

                toAppend.append(comboBoxes[1].currentIndex())

                graph[lr[0]][t[0]].append(toAppend)

        self.currentPattern.append(graph)

        interface_common.add_root(
            self.graphsTree, self.currentPattern[-1], self.tableLabels, str(len(self.currentPattern)))

        self.clear_comboboxes()
        self.clear_checkboxes()

    def clear_checkboxes(self):
        for _, _, checkBoxes, _ in self.labels:
            for cb in checkBoxes:
                cb.setChecked(False)

    def clear_comboboxes(self):
        for _, _, _, comboBoxes in self.labels:
            for comboBox in comboBoxes:
                comboBox.setCurrentIndex(0)

    def submit_pattern(self):
        patternTitle = self.patternTitle.text()
        if not patternTitle:
            return

        self.pattern_list.addItem(patternTitle)
        self.pattern_list.setCurrentRow(self.pattern_list.count() - 1)

        user_structures.add_pattern(
            self.tableName, patternTitle, self.currentPattern)
        self.patterns[patternTitle] = self.currentPattern

        self.clear_checkboxes()
        self.clear_comboboxes()
        self.patternTitle.clear()

        self.graphsTree.clear()
        self.currentPattern = []
