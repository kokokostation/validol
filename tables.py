import numpy as np
import pyqtgraph as pg

def draw_table(data, keys, title):
    table = pg.TableWidget()
    table.setWindowTitle(title)

    data = np.array([tuple([d[key] for key in keys]) for d in data], dtype=[(key, type(data[0][key])) for key in keys])

    table.setData(data)

    table.showMaximized()

    return table