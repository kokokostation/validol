import datetime as dt

import numpy as np
from PyQt5 import QtWidgets
from validol.model.utils import date_to_timestamp
from validol.view.utils.utils import set_title
from validol.view.menu.graph_dialog import GraphDialog

import validol.pyqtgraph as pg


class Table(QtWidgets.QWidget):
    def __init__(self, parent, flags, df, labels, title_info):
        QtWidgets.QWidget.__init__(self, parent, flags)

        title = GraphDialog.make_title(title_info)

        self.setWindowTitle(title)

        table = pg.TableWidget()

        cols = ["Date"] + labels

        show_df = df[labels].dropna(axis=0, how='all')

        content = np.insert(show_df.values, 0, show_df.index, axis=1).tolist()

        for i, val in enumerate(content):
            content[i] = tuple([dt.date.fromtimestamp(val[0])] + val[1:])

        data = np.array(list(map(tuple, content)),
                        dtype=list(zip(cols, [dt.date] + [float] * len(labels))))

        table.setData(data)

        self.mainLayout = QtWidgets.QVBoxLayout(self)

        set_title(self.mainLayout, title)
        self.mainLayout.addWidget(table, stretch=10)

        self.showMaximized()
