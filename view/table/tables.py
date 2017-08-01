import datetime as dt

import numpy as np
from PyQt5 import QtWidgets

import pyqtgraph as pg
from view import utils

from model.utils import date_from_timestamp, date_to_timestamp
from view.menu.graph_dialog import GraphDialog


class Table(QtWidgets.QWidget):
    def __init__(self, parent, flags, df, labels, title_info):
        QtWidgets.QWidget.__init__(self, parent, flags)

        title = GraphDialog.make_title(title_info)

        self.setWindowTitle(title)

        table = pg.TableWidget()

        date_from_timestamp(df)

        cols = ["Date"] + labels

        data = np.array(list(map(tuple, df[cols].values.tolist())),
                        dtype=list(zip(cols, [dt.date] + [float] * len(labels))))

        date_to_timestamp(df)

        table.setData(data)

        self.mainLayout = QtWidgets.QVBoxLayout(self)

        utils.set_title(self.mainLayout, title)
        self.mainLayout.addWidget(table, stretch=10)

        self.showMaximized()
