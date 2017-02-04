import numpy as np
import pyqtgraph as pg
import datetime as dt
import interface_common
from PyQt5 import QtGui

__all__ = ["draw_table"]

class Table(QtGui.QWidget):
    def __init__(self, dates, values, labels, title):
        QtGui.QWidget.__init__(self)

        self.setWindowTitle(title)

        table = pg.TableWidget()

        data = np.array([(dates[i],) + tuple(values[i]) for i in range(len(dates))], dtype=list(zip(["Date"] + labels, [dt.date] + [float] * len(labels))))

        table.setData(data)

        self.mainLayout = QtGui.QVBoxLayout(self)

        interface_common.set_title(self.mainLayout, title)
        self.mainLayout.addWidget(table, stretch=10)

        self.showMaximized()

