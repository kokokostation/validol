import datetime as dt
import math
from functools import partial

import numpy as np
import pandas as pd
from PyQt5 import QtCore, QtWidgets

import validol.pyqtgraph as pg
from validol.model.store.structures.pattern import Line, Bar
from validol.model.utils import remove_duplications
from validol.model.utils import to_timestamp
from validol.view.utils.utils import set_title
from validol.view.utils.pattern_tree import PatternTree


def negate(color):
    return [255 - rgb for rgb in color]


class MyAxisItem(pg.AxisItem):
    def __init__(self, **kargs):
        pg.AxisItem.__init__(self, **kargs)

    def tickStrings(self, values, scale, spacing):
        try:
            return [dt.date.fromtimestamp(v).isoformat() for v in values]
        except:
            return []


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


class Showable:
    def __init__(self, plot_item, chunk, showed):
        self.plot_item = plot_item
        self.chunk = chunk
        self.showed = False

        self.set(showed)

    def set(self, showed):
        if self.showed != showed:
            if showed:
                self.plot_item.addItem(self.chunk)
            else:
                self.plot_item.removeItem(self.chunk)

            self.showed = showed

    def toogle(self):
        self.set(not self.showed)


class ScatteredPlot:
    def __init__(self, plot_item, plot, scatter):
        self.plot = Showable(plot_item, plot, True)
        self.scatter = Showable(plot_item, scatter, False)
        self.scatter_state = False

    def set(self, showed):
        self.plot.set(showed)

        if self.scatter_state:
            self.scatter.set(showed)

    def toogle(self):
        self.set(not self.plot.showed)

    def toogle_scatter(self):
        self.scatter_state = not self.scatter_state

        if self.plot.showed:
            self.scatter.set(self.scatter_state)


class DaysMap:
    def __init__(self, df, pattern):
        self.start = dt.date.fromtimestamp(df.Date.iloc[0])

        days_num = (dt.date.fromtimestamp(df.Date.iloc[-1]) - self.start).days + 1 + 10
        all_dates = [to_timestamp(self.start + dt.timedelta(days=i)) for i in range(0, days_num)]

        self.days_map = pd.DataFrame(all_dates, columns=["Date"])

        self.days_map = self.days_map\
            .merge(df[['Date'] + remove_duplications(pattern.get_formulas())],
                   'outer', 'Date', sort=True)\
            .fillna(method='ffill', axis=0)

    def get_value(self, index, key):
        if 0 <= index < len(self.days_map[key]):
            return self.days_map[key][index]

    def days_passed(self, timestamp):
        try:
            date = dt.date.fromtimestamp(timestamp)
            return (date - self.start).days, to_timestamp(date), date.isoformat()
        except:
            return -1, timestamp, "None"


class Graph(pg.GraphicsWindow):
    def __init__(self, df, pattern, table_labels):
        pg.GraphicsWindow.__init__(self)

        self.widgets = {}
        self.legendData = []

        self.df = df
        self.days_map = DaysMap(df, pattern)
        self.pattern = pattern
        self.table_labels = table_labels
        self.scatter_on = False

        self.draw_graph()

    def fix(self, index):
        self.widgets[index].toogle()

    def toogle_scatter(self):
        for chunk in self.widgets.values():
            if isinstance(chunk, ScatteredPlot):
                chunk.toogle_scatter()

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

            if isinstance(piece, Line):
                pen = {'color': piece.color, 'width': 2}
                chunk = ScatteredPlot(
                    plot_item,
                    pg.PlotDataItem(xs, ys, pen=pen),
                    pg.ScatterPlotItem(xs, ys, pen=pen, size=5,
                                       brush=pg.mkBrush(color=negate(piece.color))))
            elif isinstance(piece, Bar):
                positive = list(map(lambda x: math.copysign(1, x), ys)).count(1) > len(ys) // 2
                ys = piece.sign * ys
                if not positive:
                    ys = -ys

                chunk = Showable(
                    plot_item,
                    pg.BarGraphItem(
                        x=[c + bar_width * piece.base for c in xs],
                        height=ys,
                        width=bar_width,
                        brush=pg.mkBrush(piece.color + (130,)),
                        pen=pg.mkPen('k')),
                    True)

            if isinstance(piece, Line):
                legend_color = piece.color
            elif isinstance(piece, Bar):
                legend_color = piece.color + (200,)

            self.widgets[(graph_num, piece.atom_id)] = chunk
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

        if plots:
            plots[0].setXRange(self.df.Date.iloc[0], self.df.Date.iloc[-1])

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

        def mouse_moved(evt):
            for i in range(len(plots)):
                mousePoint = plots[i].vb.mapSceneToView(evt)
                x, y = mousePoint.x(), mousePoint.y()

                days_passed, x, date = self.days_map.days_passed(int(x))

                if x == mouse_moved.prevx:
                    return

                vLines[i].setPos(x)
                hLines[i].setPos(y)
                labels[i].setPos(x, plots[i].vb.viewRange()[1][0])
                labels[i].setText(date)

                while legends[i].layout.count() > 0:
                    legends[i].removeItem(legends[i].items[0][1].text)

                legends[i].layout.setColumnSpacing(0, 20)
                for section in self.legendData[i]:
                    legends[i].addItem(*section[0])
                    for style, key in section[1:]:
                        value = self.days_map.get_value(days_passed, key)
                        if value is not None:
                            value = "{:.2f}".format(value)
                        legends[i].addItem(
                            style,
                            "{} {}".format(key, value))

        mouse_moved.prevx = None

        self.scene().sigMouseMoved.connect(mouse_moved)


class CheckedGraph(QtWidgets.QWidget):
    def __init__(self, parent, flags, df, pattern, tableLabels, title):
        QtWidgets.QWidget.__init__(self, parent, flags)

        self.setWindowTitle(title)
        self.graph = Graph(df, pattern, tableLabels)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        set_title(self.mainLayout, title)
        self.graphLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.insertLayout(1, self.graphLayout, stretch=10)

        self.left_layout = QtWidgets.QVBoxLayout(self)

        self.choiceTree = PatternTree(True)
        self.choiceTree.draw_pattern(pattern)
        self.choiceTree.itemChanged.connect(self.fix)

        self.switch_scatter_button = QtWidgets.QPushButton('Switch scatter')
        self.switch_scatter_button.clicked.connect(self.graph.toogle_scatter)

        self.left_layout.addWidget(self.choiceTree)
        self.left_layout.addWidget(self.switch_scatter_button)

        self.graphLayout.insertLayout(0, self.left_layout, stretch=1)
        self.graphLayout.addWidget(self.graph, stretch=8)

        self.showMaximized()

    def fix(self, item, i):
        self.graph.fix(item.data(0, 6))
