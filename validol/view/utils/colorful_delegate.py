from PyQt5 import QtWidgets, QtGui, QtCore
from copy import deepcopy


class ColorfulDelegate(QtWidgets.QItemDelegate):
    def __init__(self, parent=None):
        QtWidgets.QItemDelegate.__init__(self, parent)

        self.colors = None

    def set_colors(self, colors):
        self.colors = deepcopy(colors)

    def paint(self, painter, option, index):
        painter.save()

        color = self.colors[index.row()]

        if option.state & QtWidgets.QStyle.State_Selected:
            color.setAlpha(255)
        else:
            color.setAlpha(100)

        painter.setBrush(QtGui.QBrush(color))
        painter.drawRect(option.rect)

        painter.setPen(QtGui.QPen(QtCore.Qt.black))
        text = index.data(QtCore.Qt.DisplayRole)
        painter.drawText(option.rect, QtCore.Qt.AlignLeft, text)

        painter.restore()
