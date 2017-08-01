import math
from functools import partial

import numpy as np
from PyQt5 import QtCore, QtWidgets

import pyqtgraph as pg
import view.utils
from model.store.structures.pattern import Line, Bar
from view.pattern_tree import PatternTree
import datetime as dt
import pandas as pd


def negate(color):
    return [255 - rgb for rgb in color]


class MyAxisItem(pg.AxisItem):
    def __init__(self, **kargs):
        pg.AxisItem.__init__(self, **kargs)

    def tickStrings(self, values, scale, spacing):
        return [dt.date.fromtimestamp(v).isoformat() for v in values]


class MyPlot(pg.PlotItem):
    def fix_auto_range(self):
        self.enableAutoRange(y=True)

    def __init__(self, **kargs):
        pg.PlotItem.__init__(
            self, axisItems={'bottom': MyAxisItem(orientation='bottom')}, **kargs)

        self.vb.setAutoVisible(y=1)

        self.vb.sigRangeChangedManually.connect(self.fix_auto_range)


class ItemData():
    def __init__(self, symbol, brush):
        self.opts = {'symbol': symbol, 'brush': brush, 'pen': None, 'size': 20}


class DaysMap:
    DAY_SECS = 24 * 3600

    def __init__(self, df, pattern):
        self.df = df
        self.start = self.df.Date[0]

        formulas = pattern.get_formulas()
        days_num = (self.df.Date.iloc[-1] - self.df.Date.iloc[0]) // DaysMap.DAY_SECS + 1 + 7

        self.days_map = pd.DataFrame(np.full((days_num, len(formulas)), np.nan, dtype=np.double),
                                     columns=formulas)
        for col in self.days_map:
            for i, val in enumerate(self.df[col]):
                if not np.isnan(val):
                    self.days_map[col][(self.df.Date[i] - self.start) // DaysMap.DAY_SECS] = val

            curr = np.nan
            for i, val in enumerate(self.days_map[col]):
                if not np.isnan(val):
                    curr = val
                else:
                    self.days_map[col][i] = curr

    def get_value(self, timestamp, key):
        index = (timestamp - self.start) // DaysMap.DAY_SECS
        if 0 <= index < len(self.days_map[key]):
            return self.days_map[key][index]


class Graph(pg.GraphicsWindow):
    def __init__(self, df, pattern, table_labels):
        pg.GraphicsWindow.__init__(self)

        self.widgets = {}
        self.legendData = []

        self.df = df
        self.days_map = DaysMap(df, pattern)
        self.pattern = pattern
        self.table_labels = table_labels

        self.draw_graph()

    def fix(self, index, todo):
        plot_item, chunk = self.widgets[index]

        if todo:
            for item in chunk:
                plot_item.addItem(item)
        else:
            for item in chunk:
                plot_item.removeItem(item)

    def draw_axis(self, label, plot_item, graph_num, lr, pieces):
        self.legendData[graph_num][lr].append((ItemData(None, None), "____" + label + "____"))

        week = 7 * 24 * 3600
        bases = [piece.base for piece in pieces if type(piece) == Bar]
        if bases:
            bases_num = max(bases) + 1
            bar_width = 0.9 * week / bases_num

        for piece in pieces:
            xs = self.df["Date"].tolist()
            ys = np.array(self.df[piece.atom_id].tolist())

            if type(piece) == Line:
                pen = {'color': piece.color, 'width': 2}
                chunk = (pg.PlotDataItem(xs, ys, pen=pen),
                         pg.ScatterPlotItem(xs, ys, pen=pen, size=5))
            elif type(piece) == Bar:
                positive = list(map(lambda x: math.copysign(1, x), ys)).count(1) > len(ys) // 2
                ys = piece.sign * ys
                if not positive:
                    ys = -ys

                chunk = (pg.BarGraphItem(
                    x=[c + bar_width * piece.base for c in xs],
                    height=ys,
                    width=bar_width,
                    brush=pg.mkBrush(piece.color + (130,)),
                    pen=pg.mkPen('k')),)

            for item in chunk:
                plot_item.addItem(item)

            if type(piece) == Line:
                legend_color = piece.color
            elif type(piece) == Bar:
                legend_color = piece.color + (200,)

            self.widgets[(graph_num, piece.atom_id)] = (plot_item, chunk)
            self.legendData[graph_num][lr].append((ItemData('s', legend_color), piece.atom_id))

    def draw_graph(self):
        pg.setConfigOption('foreground', 'w')
        plots = []
        twins = []
        legends = []

        for i, graph in enumerate(self.pattern.graphs):
            left, right = graph.pieces
            self.legendData.append([[] for _ in range(2)])

            self.nextRow()
            plots.append(MyPlot())
            self.addItem(item=plots[-1])
            legends.append(pg.LegendItem(offset=(100, 20)))
            legends[-1].setParentItem(plots[-1])

            self.draw_axis("left", plots[-1], i, 0, left)

            twins.append(pg.ViewBox())
            plots[-1].showAxis('right')
            plots[-1].scene().addItem(twins[-1])
            plots[-1].getAxis('right').linkToView(twins[-1])
            twins[-1].setXLink(plots[-1])
            twins[-1].setAutoVisible(y=1)

            def updateViews(twin, plot):
                twin.enableAutoRange(y=True)
                twin.setGeometry(plot.vb.sceneBoundingRect())
                twin.linkedViewChanged(plot.vb, twin.XAxis)

            updateViews(twins[-1], plots[-1])
            plots[-1].vb.sigResized.connect(partial(updateViews, twins[-1], plots[-1]))

            self.draw_axis("right", twins[-1], i, 1, right)

        for i in range(len(plots)):
            for j in range(i + 1, len(plots)):
                plots[i].setXLink(plots[j])

        vLines = []
        hLines = []
        labels = []
        for p in plots:
            vLines.append(pg.InfiniteLine(angle=90, movable=False))
            hLines.append(pg.InfiniteLine(angle=0, movable=False))
            labels.append(pg.TextItem(color=(255, 255, 255), anchor=(0, 1)))
            p.addItem(vLines[-1], ignoreBounds=True)
            p.addItem(hLines[-1], ignoreBounds=True)
            p.addItem(labels[-1], ignoreBounds=True)

        def mouseMoved(evt):
            for i in range(len(plots)):
                mousePoint = plots[i].vb.mapSceneToView(evt)
                x, y = mousePoint.x(), mousePoint.y()

                vLines[i].setPos(x)
                hLines[i].setPos(y)
                labels[i].setPos(x, plots[i].vb.viewRange()[1][0])
                labels[i].setText(dt.date.fromtimestamp(int(x)).isoformat())

                while legends[i].layout.count() > 0:
                    legends[i].removeItem(legends[i].items[0][1].text)

                legends[i].layout.setColumnSpacing(0, 20)
                for section in self.legendData[i]:
                    legends[i].addItem(*section[0])
                    for style, key in section[1:]:
                        legends[i].addItem(style,
                                           "{} {}".format(key,
                                                          self.days_map.get_value(int(x), key)))

        self.scene().sigMouseMoved.connect(mouseMoved)


class CheckedGraph(QtWidgets.QWidget):
    def __init__(self, parent, flags, df, pattern, tableLabels, title):
        QtWidgets.QWidget.__init__(self, parent, flags)

        self.setWindowTitle(title)
        self.graph = Graph(df, pattern, tableLabels)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        view.utils.set_title(self.mainLayout, title)
        self.graphLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.insertLayout(1, self.graphLayout, stretch=10)

        self.choiceTree = PatternTree(True)
        self.choiceTree.draw_pattern(pattern)
        self.choiceTree.itemChanged.connect(self.fix)

        self.graphLayout.addWidget(self.choiceTree, stretch=1)
        self.graphLayout.addWidget(self.graph, stretch=8)

        self.showMaximized()

    def fix(self, item, i):
        self.graph.fix(item.data(0, 6), item.checkState(0) == QtCore.Qt.Checked)
