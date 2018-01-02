from functools import partial

from PyQt5 import QtWidgets, QtGui

from validol.model.store.structures.pattern import Graph, Line, Bar, Pattern, Indicator
from validol.model.utils.utils import remove_duplications
from validol.view.utils.utils import scrollable_area, set_title
from validol.view.utils.tipped_list import TippedList
from validol.view.utils.button_group import ButtonGroup
from validol.view.utils.pattern_tree import PatternTree
from validol.view.view_element import ViewElement


class GDTippedList(TippedList):
    def __init__(self, model_launcher, table_name):
        self.table_name = table_name

        TippedList.__init__(self, model_launcher, PatternTree(), QtWidgets.QListWidget())

    def set_view(self, item):
        self.view.draw_pattern(item)

    def get_items(self):
        return self.model_launcher.get_patterns(self.table_name)


class GraphDialog(ViewElement, QtWidgets.QWidget):
    COLORS = [(255, 0, 0), (0, 255, 255), (0, 255, 0), (255, 255, 255), (255, 255, 0),
              (255, 0, 255), (0, 0, 255), (192, 192, 192), (255, 69, 0), (255, 140, 0),
              (102, 0, 204), (51, 153, 255)]

    def __init__(self, flags, data, table_pattern, title,
                 controller_launcher, model_launcher):
        QtWidgets.QWidget.__init__(self, flags=flags)
        ViewElement.__init__(self, controller_launcher, model_launcher)

        self.setWindowTitle(table_pattern.name)

        self.data = data

        self.title = title
        self.table_name = table_pattern.name
        self.table_labels = remove_duplications(table_pattern.all_formulas())

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.upper_layout = QtWidgets.QHBoxLayout()
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.labels_layout = QtWidgets.QVBoxLayout()
        self.labels_submit_layout = QtWidgets.QVBoxLayout()
        self.patternChoiceLayout = QtWidgets.QVBoxLayout()

        set_title(self.main_layout, self.title)

        self.main_layout.insertLayout(1, self.upper_layout, stretch=10)
        self.main_layout.insertLayout(2, self.buttons_layout)

        self.tipped_list = GDTippedList(model_launcher, self.table_name)

        self.removePattern = QtWidgets.QPushButton('Remove pattern')
        self.removePattern.clicked.connect(self.remove_pattern)

        self.edit_pattern_button = QtWidgets.QPushButton('Edit pattern')
        self.edit_pattern_button.clicked.connect(self.edit_pattern)

        self.patternChoiceLayout.addWidget(self.tipped_list.list)
        self.patternChoiceLayout.addWidget(self.removePattern)
        self.patternChoiceLayout.addWidget(self.tipped_list.view)
        self.patternChoiceLayout.addWidget(self.edit_pattern_button)

        self.graphsTree = PatternTree()

        self.patternTitle = QtWidgets.QLineEdit()
        self.patternTitle.setPlaceholderText("Pattern title")
        self.labels_submit_layout.addWidget(self.patternTitle)

        self.labels_submit_layout.addWidget(
            scrollable_area(self.labels_layout))

        self.upper_layout.insertLayout(0, self.labels_submit_layout)
        self.upper_layout.addWidget(self.graphsTree)
        self.upper_layout.insertLayout(2, self.patternChoiceLayout)

        self.submitPattern = QtWidgets.QPushButton('Submit pattern')
        self.submitPattern.clicked.connect(self.submit_pattern)

        self.drawGraph = QtWidgets.QPushButton('Draw graph')
        self.drawGraph.clicked.connect(self.draw_graph)

        self.buttons_layout.addWidget(self.submitPattern)
        self.buttons_layout.addWidget(self.drawGraph)

        self.graphs = []

        self.labels = []

        for i, label in enumerate(self.table_labels):
            lastLabel = QtWidgets.QHBoxLayout()

            textBox = QtWidgets.QLineEdit()
            textBox.setReadOnly(True)
            textBox.setText(label)
            lastLabel.addWidget(textBox)

            groups = [["left", "right"], ["line", "bar", "-bar", "ind"], ["show"]]


            button_groups = [ButtonGroup([QtWidgets.QCheckBox(label) for label in group])
                             for group in groups]
            for bg in button_groups:
                for item in bg.buttons:
                    lastLabel.addWidget(item)

            comboBoxes = [QtWidgets.QComboBox() for _ in range(2)]
            for comboBox in comboBoxes:
                model = comboBox.model()
                for color in GraphDialog.COLORS:
                    item = QtGui.QStandardItem("")
                    item.setBackground(QtGui.QColor(*color))
                    model.appendRow(item)

                comboBox.currentIndexChanged.connect(partial(self.indexChanged, comboBox))
                comboBox.highlighted.connect(partial(self.activated, comboBox))
                self.indexChanged(comboBox, 0)

                lastLabel.addWidget(comboBox)

            self.labels.append((textBox, button_groups, comboBoxes))

            self.labels_layout.insertLayout(i, lastLabel)

        self.submitGraph = QtWidgets.QPushButton('Submit graph')
        self.submitGraph.clicked.connect(self.submit_graph)
        self.labels_submit_layout.addWidget(self.submitGraph)

        self.currentPattern = Pattern()

        self.showMaximized()

    def remove_pattern(self):
        self.model_launcher.remove_pattern(self.tipped_list.current_item())
        self.tipped_list.refresh()

    def activated(self, comboBox, _=None):
        comboBox.setStyleSheet("color: white; background-color: transparent")

    def indexChanged(self, comboBox, color):
        comboBox.setStyleSheet(
            "color: white; background-color: rgb" + str(GraphDialog.COLORS[color]))

    def draw_graph(self):
        if self.tipped_list.current_item() is not None:
            self.controller_launcher.draw_graph(self.data,
                                                self.tipped_list.current_item(),
                                                self.table_labels,
                                                self.title)

    def submit_graph(self):
        base_colors = []

        graph = Graph()

        for i, label in enumerate(self.labels):
            name, button_groups, combo_boxes = label
            lr, typ = button_groups[0].checked_button(), button_groups[1].checked_button()
            show = button_groups[2].checked_button() is not None

            if typ:
                color = GraphDialog.COLORS[combo_boxes[1].currentIndex()]

                if typ[1] == "ind":
                    graph.add_piece(0, Indicator(name.text(), color, show))
                elif lr:
                    if typ[1] == "line":
                        graph.add_piece(lr[0], Line(name.text(), color, show))
                    else:
                        base_color = combo_boxes[0].currentIndex()

                        if base_color in base_colors:
                            base = base_colors.index(base_color)
                        else:
                            base = len(base_colors)
                            base_colors.append(base_color)

                        sign = 1
                        if typ[1] == "-bar":
                            sign = -1

                        graph.add_piece(lr[0], Bar(name.text(), color, base, sign, show))

        self.currentPattern.add_graph(graph)

        self.graphsTree.add_root(
            self.currentPattern.graphs[-1],
            str(len(self.currentPattern.graphs)))

        self.clear_comboboxes()
        self.clear_checkboxes()

    def clear_checkboxes(self):
        for _, button_groups, _ in self.labels:
            for bg in button_groups:
                bg.clear()

    def clear_comboboxes(self):
        for _, _, comboBoxes in self.labels:
            for comboBox in comboBoxes:
                comboBox.setCurrentIndex(0)

    def submit_pattern(self):
        patternTitle = self.patternTitle.text()
        if not patternTitle or not self.currentPattern.graphs:
            return

        self.currentPattern.set_name(self.table_name, patternTitle)

        self.model_launcher.write_pattern(self.currentPattern)
        self.tipped_list.refresh()

        self.clear_checkboxes()
        self.clear_comboboxes()
        self.patternTitle.clear()

        self.graphsTree.clear()
        self.currentPattern = Pattern()

    def edit_pattern(self):
        pattern = self.model_launcher.read_str_pattern(self.tipped_list.current_item())

        edited = self.controller_launcher.edit_pattern(pattern.graphs)

        if edited is not None:
            pattern.graphs = edited

            self.model_launcher.write_str_pattern(pattern)

            self.tipped_list.refresh()

