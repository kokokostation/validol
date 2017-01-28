from PyQt4 import QtGui, QtCore
import parser
import tables
import graphs
import utils
import downloader

class Window(QtGui.QWidget):
    def __init__(self, app):
        QtGui.QWidget.__init__(self)

        self.grabber = parser.Grabber()

        self.app = app

        self.setWindowTitle("BatyaGraphs")

        self.platforms = QtGui.QListWidget()
        self.platforms.itemClicked.connect(self.platform_chosen)
        for code, name in parser.get_platforms():
            wi = QtGui.QListWidgetItem(name)
            wi.setToolTip(code)
            self.platforms.addItem(wi)

        self.actives = QtGui.QListWidget()

        self.cached_prices = QtGui.QListWidget()
        for url, name in parser.get_cached_prices():
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
        data, name, url, new = self.grabber.get_table1(chosen_platform, chosen_active, url_widget.text())
        if new:
            wi = QtGui.QListWidgetItem(name)
            wi.setToolTip(url)
            self.cached_prices.addItem(wi)

        title = chosen_platform_name + "/" + chosen_active + "; Price: " + name

        self.table = tables.draw_table(data, parser.table1_labels, title)
        self.win = GraphDialog("table1", parser.table1_labels[1:], data, title, self.grabber)

    def on_update(self):
        self.updateButton.setText("Wait. Updating the data...")
        self.app.processEvents()
        downloader.update()
        self.updateButton.setText("Update")

class GraphDialog(QtGui.QWidget):
    def __init__(self, tableName, tableLabels, data, title, grabber):
        QtGui.QWidget.__init__(self)

        title = tableName + " " + title
        self.setWindowTitle(title)

        self.data = data
        self.title = title
        self.grabber = grabber
        self.tableName = tableName

        self.main_layout = QtGui.QVBoxLayout(self)
        self.upper_layout = QtGui.QHBoxLayout()
        self.labels_layout = QtGui.QVBoxLayout()
        self.buttons_layout = QtGui.QHBoxLayout()

        self.main_layout.insertLayout(0, self.upper_layout)
        self.main_layout.insertLayout(1, self.buttons_layout)

        self.pattern_list = QtGui.QListWidget()
        if tableName in grabber.patterns:
            for graphName in grabber.patterns[tableName].keys():
                self.pattern_list.addItem(graphName)

        self.graphsTree = QtGui.QTreeWidget()

        self.upper_layout.insertLayout(0, self.labels_layout)
        self.upper_layout.addWidget(self.graphsTree)
        self.upper_layout.addWidget(self.pattern_list)

        self.submitPattern = QtGui.QPushButton('Submit pattern')
        self.submitPattern.clicked.connect(self.submit_pattern)

        self.drawGraph = QtGui.QPushButton('Draw graph')
        self.drawGraph.clicked.connect(self.draw_graph)

        self.buttons_layout.addWidget(self.submitPattern)
        self.buttons_layout.addWidget(self.drawGraph)

        self.patternTitle = QtGui.QLineEdit()
        self.patternTitle.setText("Pattern title")
        self.labels_layout.addWidget(self.patternTitle)

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
                for i in t:
                    buttonGroups[-1].add_item(checkBoxes[i])
                    lastLabel.addWidget(checkBoxes[i])

            self.labels.append((textBox, buttonGroups, checkBoxes))

            self.labels_layout.insertLayout(i, lastLabel)

        self.submitGraph = QtGui.QPushButton('Submit graph')
        self.submitGraph.clicked.connect(self.submit_graph)
        self.labels_layout.addWidget(self.submitGraph)

        self.currentPattern = []

        self.showMaximized()

    def draw_graph(self):
        self.graph = graphs.CheckedGraph(self.data, self.grabber.patterns[self.tableName][self.pattern_list.currentItem().text()], self.title)

    def submit_graph(self):
        root = QtGui.QTreeWidgetItem([str(len(self.currentPattern))])
        children = [QtGui.QTreeWidgetItem([label]) for label in ["left", "right"]]
        types = [[QtGui.QTreeWidgetItem([label]) for label in ["line", "bar", "-bar"]] for _ in range(len(children))]

        graph = [[[] for _ in range(3)] for _ in range(2)]
        for textBox, buttonGroups, _ in self.labels:
            lr, t = buttonGroups[0].checked_button(), buttonGroups[1].checked_button()
            if lr and t:
                graph[lr[0]][t[0]].append(textBox.text())

                types[lr[0]][t[0]].addChild(QtGui.QTreeWidgetItem([textBox.text() + " " + t[1]]))

        self.currentPattern.append(graph)

        for i in range(len(children)):
            for j in range(len(types[i])):
                children[i].addChild(types[i][j])

        for item in children:
            root.addChild(item)

        self.graphsTree.addTopLevelItem(root)
        root.setExpanded(True)
        for i in range(root.childCount()):
            root.child(i).setExpanded(True)
            for j in range(root.child(i).childCount()):
                root.child(i).child(j).setExpanded(True)
        self.clear_checkboxes()

    def clear_checkboxes(self):
        for _, _, checkBoxes in self.labels:
            for cb in checkBoxes:
                cb.setChecked(False)

    def submit_pattern(self):
        patternTitle = self.patternTitle.text()
        self.pattern_list.addItem(patternTitle)

        utils.add_to_dict(self.grabber.patterns, self.tableName, patternTitle, self.currentPattern)

        parser.add_pattern(self.tableName, patternTitle, self.currentPattern)

        self.clear_checkboxes()

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
