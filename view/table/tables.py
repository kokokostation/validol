import datetime as dt

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtWidgets

from view import utils


class Table(QtWidgets.QWidget):
    def __init__(self, parent, flags, dates, values, labels, title):
        QtWidgets.QWidget.__init__(self, parent, flags)

        self.setWindowTitle(title)

        table = pg.TableWidget()

        data = np.array([(dates[i],) + tuple(values[i]) for i in range(len(dates))],
                        dtype=list(zip(["Date"] + labels, [dt.date] + [float] * len(labels))))

        table.setData(data)

        self.mainLayout = QtWidgets.QVBoxLayout(self)

        utils.set_title(self.mainLayout, title)
        self.mainLayout.addWidget(table, stretch=10)

        self.showMaximized()
