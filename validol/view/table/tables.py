import datetime as dt
from PyQt5 import QtWidgets, QtGui
import numpy as np
import pandas as pd

from validol.view.utils.utils import set_title
from validol.view.menu.graph_dialog import GraphDialog

import validol.pyqtgraph as pg

class Table(QtWidgets.QWidget):
    def __init__(self, flags, df, labels, title):
        QtWidgets.QWidget.__init__(self, flags=flags)

        self.setWindowTitle(title)

        table = pg.TableWidget()

        filtered_df = df[labels].dropna(axis=0, how='all')

        show_df = filtered_df.copy()
        show_df.index = show_df.index.map(dt.date.fromtimestamp)

        for col in show_df:
            if show_df[col].dtype == np.float64:
                show_df[col] = show_df[col].apply("{:.2f}".format)

        table.setData(show_df.to_records())

        for i, col in enumerate(filtered_df):
            col_without_nan = filtered_df[col].dropna()

            if not col_without_nan.empty:
                min_val, max_val = col_without_nan.min(), col_without_nan.max()

                if max_val != min_val:
                    for j in range(len(filtered_df)):
                        value = filtered_df.iloc[j, i]

                        if value is not None and not pd.isnull(value):
                            try:
                                norm = (value - min_val) / (max_val - min_val)
                                table.item(j, i + 1).setBackground(
                                    QtGui.QBrush(QtGui.QColor(*map(int, [255 * norm, 0, 255 * (1 - norm), 100]))))
                            except:
                                pass

        self.mainLayout = QtWidgets.QVBoxLayout(self)

        set_title(self.mainLayout, title)
        self.mainLayout.addWidget(table, stretch=10)

        self.showMaximized()
