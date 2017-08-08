from PyQt5 import QtWidgets, QtCore


class PatternTree(QtWidgets.QTreeWidget):
    def __init__(self, checkable=False):
        QtWidgets.QTreeWidget.__init__(self)

        self.checkable = checkable

    def add_root(self, graph, label):
        root = QtWidgets.QTreeWidgetItem([label])
        children = [QtWidgets.QTreeWidgetItem([label]) for label in ["left", "right"]]

        for i in range(2):
            types = dict((label, QtWidgets.QTreeWidgetItem([label]))
                         for label in ("line", "bar", "-bar"))
            for piece in graph.pieces[i]:
                item = QtWidgets.QTreeWidgetItem([piece.atom_id])

                if self.checkable:
                    item.setCheckState(0, QtCore.Qt.Checked)
                    item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                    item.setData(0, 6, (self.topLevelItemCount(), piece.atom_id))

                types[piece.name()].addChild(item)
                children[i].addChild(types[piece.name()])
            root.addChild(children[i])

        self.addTopLevelItem(root)

        root.setExpanded(True)
        for i in range(root.childCount()):
            root.child(i).setExpanded(True)
            for j in range(root.child(i).childCount()):
                root.child(i).child(j).setExpanded(True)

    def draw_pattern(self, pattern):
        for i, graph in enumerate(pattern.graphs):
            self.add_root(graph, str(i))