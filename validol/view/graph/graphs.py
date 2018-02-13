import datetime as dt
import math
from functools import partial
import numpy as np
import pandas as pd
from PyQt5 import QtCore, QtWidgets
from collections import defaultdict

import validol.pyqtgraph as pg
from validol.model.store.structures.pattern import Line, Bar, Indicator
from validol.model.utils.utils import remove_duplications, to_timestamp, merge_dfs
from validol.view.utils.utils import set_title, showable_df
from validol.view.utils.pattern_tree import PatternTree
from validol.view.view_element import ViewElement


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


class GraphItem:
    def __init__(self, flavor):
        self.flavor = flavor

    def showed(self):
        raise NotImplementedError

    def toogle(self):
        raise NotImplementedError

    def redraw(self):
        if self.showed():
            for _ in range(2):
                self.toogle()


class Showable(GraphItem):
    def __init__(self, plot_item, chunks, showed, flavor=None):
        GraphItem.__init__(self, flavor)

        self.plot_item = plot_item
        self.chunks = chunks
        self.showed_ = False

        self.set(showed)

    def set(self, showed):
        if self.showed_ != showed:
            for chunk in self.chunks:
                if showed:
                    self.plot_item.addItem(chunk)
                else:
                    self.plot_item.removeItem(chunk)

            self.showed_ = showed

    def toogle(self):
        self.set(not self.showed_)

    def showed(self):
        return self.showed_


class ScatteredPlot(GraphItem):
    def __init__(self, plot_item, plot, scatter, showed, flavor):
        GraphItem.__init__(self, flavor)

        self.plot = Showable(plot_item, [plot], showed)
        self.scatter = Showable(plot_item, [scatter], False)
        self.scatter_state = False

    def set(self, showed):
        self.plot.set(showed)

        if self.scatter_state:
            self.scatter.set(showed)

    def toogle(self):
        self.set(not self.plot.showed_)

    def toogle_scatter(self):
        self.scatter_state = not self.scatter_state

        if self.plot.showed_:
            self.scatter.set(self.scatter_state)

    def showed(self):
        return self.plot.showed_


class DaysMap:
    def __init__(self, data, pattern):
        self.start = dt.date.fromtimestamp(data.df.index[0])

        days_num = (dt.date.fromtimestamp(data.df.index[-1]) - self.start).days + 1 + 10
        all_dates = [to_timestamp(self.start + dt.timedelta(days=i)) for i in range(0, days_num)]

        formulas = remove_duplications(pattern.get_formulas())

        self.days_map = merge_dfs(pd.DataFrame(index=all_dates), data.df[formulas])

        for formula in formulas:
            method = 'ffill'

            if formula in data.info:
                method = data.info[formula].get('fill_method', 'ffill')

            self.days_map[formula].fillna(method=method, axis=0, inplace=True)

        self.days_map = showable_df(self.days_map)

        self.days_map.index = np.arange(len(self.days_map))

    def get_value(self, index, key):
        if 0 <= index < len(self.days_map[key]):
            return self.days_map.loc[index, key]

    def days_passed(self, timestamp):
        try:
            date = dt.date.fromtimestamp(timestamp)
            return (date - self.start).days, to_timestamp(date), date.isoformat()
        except:
            return -1, timestamp, "None"


class LegendUpdater:
    DELAY = 200

    def __init__(self, data, pattern, vert_lines, hor_lines, plots, legends, labels, legend_data):
        self.days_map = DaysMap(data, pattern)
        self.vert_lines = vert_lines
        self.hor_lines = hor_lines
        self.plots = plots
        self.legends = legends
        self.labels = labels
        self.legend_data = legend_data

        self.prevt = dt.datetime.now() - dt.timedelta(microseconds=LegendUpdater.DELAY * 1000)

        self.qtimer = QtCore.QTimer()
        self.qtimer.setSingleShot(True)
        self.qtimer.setInterval(LegendUpdater.DELAY)
        self.qtimer.timeout.connect(lambda: self.set_legend(None))

        self.curr_days_passed = None

    def mouse_moved(self, event):
        x = self.plots[0].vb.mapSceneToView(event).x()
        days_passed, x, date = self.days_map.days_passed(int(x))

        self.set_lines(x, date, event)

        if (dt.datetime.now() - self.prevt).microseconds >= LegendUpdater.DELAY * 1000:
            self.qtimer.stop()
            self.set_legend(days_passed)
        else:
            self.curr_days_passed = days_passed
            if not self.qtimer.isActive():
                self.qtimer.start()

    def set_legend(self, days_passed):
        for i in range(len(self.plots)):
            while self.legends[i].layout.count() > 0:
                self.legends[i].removeItem(self.legends[i].items[0][1].text)

            self.legends[i].layout.setColumnSpacing(0, 20)
            for section in self.legend_data[i]:
                self.legends[i].addItem(*section[0])
                for style, key in section[1:]:
                    value = self.days_map.get_value(days_passed or self.curr_days_passed, key)
                    self.legends[i].addItem(
                        style,
                        "{} {}".format(key, value))

        self.prevt = dt.datetime.now()

    def set_lines(self, x, date, event):
        for i, plot in enumerate(self.plots):
            y = plot.vb.mapSceneToView(event).y()

            self.vert_lines[i].setPos(x)
            self.hor_lines[i].setPos(y)
            self.labels[i].setPos(x, plot.vb.viewRange()[1][0])
            self.labels[i].setText(date)


class Graph(pg.GraphicsWindow):
    def __init__(self, data, pattern, table_labels):
        pg.GraphicsWindow.__init__(self)

        self.widgets = defaultdict(dict)
        self.legendData = []

        self.data = data
        self.pattern = pattern
        self.table_labels = table_labels
        self.scatter_on = False

        self.draw_graph()

    def fix(self, index):
        graph_num, atom_id = index

        wi = self.widgets[graph_num][atom_id]

        wi.toogle()

        if wi.flavor == 'bar' and wi.showed():
            self.fix_background(graph_num)

    def fix_background(self, graph_num):
        for w in self.widgets[graph_num].values():
            if w.flavor != 'bar':
                w.redraw()

    def toogle_scatter(self):
        for d in self.widgets.values():
            for chunk in d.values():
                if isinstance(chunk, ScatteredPlot):
                    chunk.toogle_scatter()

    def draw_axis(self, plot_items, graph_num, graph_pieces):
        bars = [piece for pieces in graph_pieces for piece in pieces if isinstance(piece, Bar)]
        if bars:
            week = pd.Series(
                self.data.df[[piece.atom_id for piece in bars]].dropna(how='all').index).diff().min()
            bases_num = max([piece.base for piece in bars]) + 1
            bar_width = 0.95 * week / bases_num

        for lr, (plot_item, pieces, label) in enumerate(zip(plot_items, graph_pieces, ('left', 'right'))):
            self.legendData[graph_num][lr].append((ItemData(None, None), "____" + label + "____"))

            for piece in pieces:
                if isinstance(piece, Line) or isinstance(piece, Bar):
                    xs = pd.Series(self.data.df.index).as_matrix()
                    ys = self.data.df[piece.atom_id].as_matrix().astype(np.float64)

                if isinstance(piece, Line):
                    pen = {'color': piece.color, 'width': 2}
                    chunk = ScatteredPlot(
                        plot_item,
                        pg.PlotDataItem(xs, ys, pen=pen),
                        pg.ScatterPlotItem(xs, ys, pen=pen, size=5,
                                           brush=pg.mkBrush(color=negate(piece.color))),
                        piece.show,
                        'line')
                    legend_color = piece.color
                elif isinstance(piece, Bar):
                    positive = list(map(lambda x: math.copysign(1, x), ys)).count(1) > len(ys) // 2
                    ys = piece.sign * ys
                    if not positive:
                        ys = -ys

                    chunk = Showable(
                        plot_item,
                        [pg.BarGraphItem(
                            x=xs + bar_width * piece.base,
                            height=ys,
                            width=bar_width,
                            brush=pg.mkBrush(piece.color + [130]),
                            pen=pg.mkPen('k'))],
                        piece.show,
                        'bar'
                    )
                    legend_color = piece.color + [200]
                elif isinstance(piece, Indicator):
                    pen = {'color': piece.color, 'width': 2}
                    chunk = Showable(
                        plot_item,
                        [pg.VTickGroup([date for date, _ in
                                        self.data.df[piece.atom_id].dropna().iteritems()],
                                       [0, 0.1],
                                       pen=pen)],
                        piece.show,
                        'indicator'
                    )
                    legend_color = piece.color

                self.widgets[graph_num][piece.atom_id] = chunk
                self.legendData[graph_num][lr].append((ItemData('s', legend_color), piece.atom_id))

        self.fix_background(graph_num)

    def draw_graph(self):
        pg.setConfigOption('foreground', 'w')
        plots = []
        twins = []
        legends = []

        for i, graph in enumerate(self.pattern.graphs):
            self.legendData.append([[] for _ in range(2)])

            self.nextRow()
            plots.append(MyPlot())
            self.addItem(item=plots[-1])
            legends.append(pg.LegendItem(offset=(100, 20)))
            legends[-1].setParentItem(plots[-1])

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

            self.draw_axis([plots[-1], twins[-1]], i, graph.pieces)

        for i in range(len(plots)):
            for j in range(i + 1, len(plots)):
                plots[i].setXLink(plots[j])

        if plots:
            plots[0].setXRange(self.data.df.index[0], self.data.df.index[-1])

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

        self.legend_updater = LegendUpdater(self.data, self.pattern, vLines, hLines,
                                            plots, legends, labels, self.legendData)

        self.scene().sigMouseMoved.connect(self.legend_updater.mouse_moved)


class CheckedGraph(ViewElement, QtWidgets.QWidget):
    def __init__(self, flags, data, pattern, tableLabels, title, controller_launcher, model_launcher):
        QtWidgets.QWidget.__init__(self, flags=flags)
        ViewElement.__init__(self, controller_launcher, model_launcher)

        self.setWindowTitle(title)
        self.graph = Graph(data, pattern, tableLabels)

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
