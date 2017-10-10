from PyQt5 import QtWidgets, QtGui
import pandas as pd
import numpy as np

from validol.view.utils.utils import set_title

import validol.pyqtgraph as pg


class Table(QtWidgets.QWidget):
    def __init__(self, flags, data, labels, title):
        QtWidgets.QWidget.__init__(self, flags=flags)

        self.setWindowTitle(title)

        table = pg.TableWidget()

        df = data.df[labels]

        table.setData(data.show_df[['Date'] + labels].to_records(index=False))

        for i, col in enumerate(df):
            if not np.issubdtype(df[col].dtype, np.number):
                continue

            col_without_nan = df[col].dropna()

            if col_without_nan.empty:
                continue

            min_val, max_val = col_without_nan.min(), col_without_nan.max()

            if max_val != min_val:
                for j in range(len(df)):
                    value = df.iloc[j, i]

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
