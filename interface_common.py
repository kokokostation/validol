from PyQt5 import QtGui, QtCore

__all__ = ["add_root", "draw_pattern", "set_title"]

def add_root(tree, graph, tableLabels, label, info=None, current=None, checkable=False):
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
                if info:
                    info[item] = current
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

    if info:
        return current

def draw_pattern(tree, pattern, tableLabels, checkable=False):
    current = 0
    info = {}
    for i in range(len(pattern)):
        current = add_root(tree, pattern[i], tableLabels, str(i), info, current, checkable)

    return info

def set_title(layout, title):
    denotions = QtGui.QTextEdit()
    denotions.setText(title)
    denotions.setReadOnly(True)
    layout.addWidget(denotions, stretch=1)
