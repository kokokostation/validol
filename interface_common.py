from PyQt5 import QtGui, QtCore

__all__ = ["add_root", "draw_pattern", "set_title"]

def scrollable_area(layout):
    scroll = QtGui.QScrollArea()
    scroll.setWidgetResizable(True)
    inner = QtGui.QFrame(scroll)
    inner.setLayout(layout)
    scroll.setWidget(inner)
    return scroll

def add_root(tree, graph, tableLabels, label, current=None, checkable=False):
    root = QtGui.QTreeWidgetItem([label])
    children = [QtGui.QTreeWidgetItem([label]) for label in ["left", "right"]]

    for j in range(2):
        types = [QtGui.QTreeWidgetItem([label]) for label in ["line", "bar", "-bar"]]
        for k in range(3):
            for piece in graph[j][k]:
                if type(piece) == int:
                    index = piece
                else:
                    index = piece[0]

                item = QtGui.QTreeWidgetItem([tableLabels[index]])
                if current != None:
                    item.setToolTip(0, str(current))
                    current += 1

                if checkable:
                    item.setCheckState(0, QtCore.Qt.Checked)
                    item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                types[k].addChild(item)
            children[j].addChild(types[k])
        root.addChild(children[j])

    tree.addTopLevelItem(root)

    root.setExpanded(True)
    for i in range(root.childCount()):
        root.child(i).setExpanded(True)
        for j in range(root.child(i).childCount()):
            root.child(i).child(j).setExpanded(True)
    if current != None:
        return current

def draw_pattern(tree, pattern, tableLabels, checkable=False):
    current = 0
    for i in range(len(pattern)):
        current = add_root(tree, pattern[i], tableLabels, str(i), current, checkable)


def set_title(layout, title):
    denotions = QtGui.QTextEdit()
    denotions.setText(title)
    denotions.setReadOnly(True)
    layout.addWidget(denotions, stretch=1)

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
