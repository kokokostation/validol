import numpy as np
import pyqtgraph as pg
import datetime as dt

__all__ = ["draw_table"]

def draw_table(dates, values, labels, title):
    table = pg.TableWidget()
    table.setWindowTitle(title)

    data = np.array([(dates[i],) + tuple(values[i]) for i in range(len(data))], dtype=list(zip(["Date"] + labels, [dt.date] + [float] * len(labels))))

    table.setData(data)

    table.showMaximized()

    return table