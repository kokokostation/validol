import math
from functools import partial

import numpy as np
from PyQt5 import QtCore, QtWidgets

import pyqtgraph as pg
import view.utils
from model.store.structures.pattern import Line, Bar
from model.utils import split, none_filter
from view.pattern_tree import PatternTree

colors = [(255, 0, 0), (0, 255, 255), (0, 255, 0), (255, 255, 255),
          (255, 255, 0), (255, 0, 255), (0, 0, 255)]


def negate(color):
    return [255 - rgb for rgb in color]


class MyAxisItem(pg.AxisItem):
    def __init__(self, str_dates, **kargs):
        pg.AxisItem.__init__(self, **kargs)
        self.str_dates = str_dates

    def tickStrings(self, values, scale, spacing):
        result = []
        for v in values:
            if 0 <= v < len(self.str_dates):
                result.append(self.str_dates[int(v)])
            else:
                result.append('')
        return result


class MyPlot(pg.PlotItem):
    def fixAutoRange(self):
        self.enableAutoRange(y=True)

    def __init__(self, str_dates, **kargs):
        pg.PlotItem.__init__(
            self, axisItems={'bottom': MyAxisItem(str_dates, orientation='bottom')}, **kargs)

        self.vb.setAutoVisible(y=1)

        self.vb.sigRangeChangedManually.connect(self.fixAutoRange)


class ItemData():
    def __init__(self, symbol, brush):
        self.opts = {'symbol': symbol, 'brush': brush, 'pen': None, 'size': 20}


class Graph(pg.GraphicsWindow):
    def __init__(self, dates, values, pattern, tableLabels):
        pg.GraphicsWindow.__init__(self)

        self.widgets = {}
        self.legendData = []

        self.dates = dates
        self.values = values
        self.pattern = pattern
        self.tableLabels = tableLabels

        self.draw_graph()

    def fix(self, index, todo):
        plotItem, plots = self.widgets[index]

        for plot in plots:
            if todo == True:
                plotItem.addItem(plot)
            else:
                plotItem.removeItem(plot)

    def draw_axis(self, label, plotItem, graph_num, lr, pieces):
        self.legendData[graph_num][lr].append((ItemData(None, None), "____" + label + "____"))

        bases = [piece.base for piece in pieces if type(piece) == Bar]
        if bases:
            bases_num = max(bases) + 1
            bar_width = 0.9 / bases_num

        for piece in pieces:
            chunks = []

            for chain in split([i if self.values[i][piece.atom_id] is not None else None for i in range(len(self.values))], None):
                if chain:
                    ys = np.array([self.values[i][piece.atom_id] for i in chain])

                    if type(piece) == Line:
                        chunks.append(pg.PlotDataItem(
                            chain,
                            ys,
                            pen={'color': colors[piece.color], 'width': 2}))
                    elif type(piece) == Bar:
                        positive = list(map(lambda x: math.copysign(1, x), ys)).count(1) > len(ys) // 2
                        ys = piece.sign * ys
                        if not positive:
                            ys = -ys

                        chunks.append(pg.BarGraphItem(
                            x=[c + bar_width * piece.base for c in chain],
                            height=ys,
                            width=bar_width,
                            brush=pg.mkBrush(colors[piece.color] + (130,)),
                            pen=pg.mkPen('k')))

                    plotItem.addItem(chunks[-1])

            if type(piece) == Line:
                legend_color = colors[piece.color]
            elif type(piece) == Bar:
                legend_color = colors[piece.color] + (200,)

            self.widgets[(graph_num, piece.atom_id)] = (plotItem, chunks)
            self.legendData[graph_num][lr].append((ItemData('s', legend_color), piece.atom_id))

    def draw_graph(self):
        pg.setConfigOption('foreground', 'w')
        plots = []
        twins = []
        legends = []

        str_dates = [date.strftime("%d/%m/%Y") for date in self.dates]

        for i, graph in enumerate(self.pattern.graphs):
            left, right = graph.pieces
            self.legendData.append([[] for _ in range(2)])

            self.nextRow()
            plots.append(MyPlot(str_dates))
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
            plots[0].setXRange(0, len(str_dates))

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
                if 0 <= int(x) < len(str_dates) and mouseMoved.prevxs[i] != int(x):
                    labels[i].setText(str_dates[int(x)])

                    while legends[i].layout.count() > 0:
                        legends[i].removeItem(legends[i].items[0][1].text)

                    for section in self.legendData[i]:
                            legends[i].addItem(section[0][0], section[0][1])
                            for style, key in section[1:]:
                                legends[i].addItem(style, "{} {}".format(self.tableLabels[key], none_filter(round)(self.values[int(x)][key], 2)))
                                legends[i].layout.setColumnSpacing(0, 20)

                    mouseMoved.prevxs[i] = int(x)

        mouseMoved.prevxs = [None] * len(plots)

        self.scene().sigMouseMoved.connect(mouseMoved)


class CheckedGraph(QtWidgets.QWidget):
    def __init__(self, parent, flags, dates, values, pattern, tableLabels, title):
        QtWidgets.QWidget.__init__(self, parent, flags)

        self.setWindowTitle(title)
        self.graph = Graph(dates, values, pattern, tableLabels)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        view.utils.set_title(self.mainLayout, title)
        self.graphLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.insertLayout(1, self.graphLayout, stretch=10)

        self.choiceTree = PatternTree(True)
        self.choiceTree.draw_pattern(pattern, tableLabels)
        self.choiceTree.itemChanged.connect(self.fix)

        self.graphLayout.addWidget(self.choiceTree, stretch=1)
        self.graphLayout.addWidget(self.graph, stretch=8)

        self.showMaximized()

    def fix(self, item, i):
        self.graph.fix(item.data(0, 6), item.checkState(0) == QtCore.Qt.Checked)
