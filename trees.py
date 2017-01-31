from PyQt5 import QtGui, QtCore

__all__ = ["add_root", "draw_pattern"]

def add_root(tree, graph, label, checkable=False):
    root = QtGui.QTreeWidgetItem([label])
    children = [QtGui.QTreeWidgetItem([label]) for label in ["left", "right"]]

    for j in range(2):
        types = [QtGui.QTreeWidgetItem([label]) for label in ["line", "bar", "-bar"]]
        for k in range(3):
            for label in graph[j][k]:
                item = QtGui.QTreeWidgetItem([str(label)])
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

def draw_pattern(tree, pattern, checkable=False):
    for i in range(len(pattern)):
        add_root(tree, pattern[i], str(i), checkable)
