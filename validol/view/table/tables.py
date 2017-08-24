import datetime as dt
from PyQt5 import QtWidgets
import numpy as np

from validol.view.utils.utils import set_title
from validol.view.menu.graph_dialog import GraphDialog

import validol.pyqtgraph as pg

class Table(QtWidgets.QWidget):
    def __init__(self, flags, df, labels, title_info):
        QtWidgets.QWidget.__init__(self, flags=flags)

        title = GraphDialog.make_title(title_info)

        self.setWindowTitle(title)

        table = pg.TableWidget()

        show_df = df[labels].dropna(axis=0, how='all')
        show_df.index = show_df.index.map(dt.date.fromtimestamp)

        for col in show_df:
            if show_df[col].dtype == np.float64:
                show_df[col] = show_df[col].apply("{:.2f}".format)

        table.setData(show_df.to_records())

        self.mainLayout = QtWidgets.QVBoxLayout(self)

        set_title(self.mainLayout, title)
        self.mainLayout.addWidget(table, stretch=10)

        self.showMaximized()
