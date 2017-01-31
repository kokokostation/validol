import numpy as np
import pyqtgraph as pg

__all__ = ["draw_table"]

def draw_table(data, keys, key_types, title):
    table = pg.TableWidget()
    table.setWindowTitle(title)

    data = np.array([tuple([d[key] if key in d else None for key in keys]) for d in data], dtype=list(zip(keys, key_types)))

    table.setData(data)

    table.showMaximized()

    return table