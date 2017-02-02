from PyQt4 import QtGui, QtCore
import pyqtgraph as pg
import math
import utils
import data_parser
import interface_common
from functools import partial

__all__ = ["CheckedGraph", "colors", "qcolors"]

colors = [(255, 0, 0), (0, 255, 255), (0, 255, 0), (255, 255, 255), (255, 255, 0), (255, 0, 255), (0, 0, 255)]
qcolors = ["black", "cyan", "red", "magenta", "green", "yellow"]

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
        pg.PlotItem.__init__(self, axisItems={'bottom': MyAxisItem(str_dates, orientation='bottom')}, **kargs)

        self.vb.setAutoVisible(y=1)

        self.vb.sigRangeChangedManually.connect(self.fixAutoRange)

class ItemData():
    def __init__(self, symbol, brush):
        self.opts = {'symbol': symbol, 'brush': brush, 'pen': None, 'size': 20}

class Graph(pg.GraphicsWindow):
    def __init__(self, dates, values, pattern, tableLabels):
        pg.GraphicsWindow.__init__(self)

        self.widgets = []

        self.dates = dates
        self.values = values
        self.pattern = pattern
        self.tableLabels = tableLabels

        self.draw_graph()

    def fix(self, index, toDo):
        plotItem, plots = self.widgets[index]

        for plot in plots:
            if toDo == True:
                plotItem.addItem(plot)
            else:
                plotItem.removeItem(plot)

    def draw_axis(self, label, legend, plotItem, color, lines, bars, mbars):
        legend.addItem(ItemData(None, None), "____" + label + "____")

        #code duplication
        for key in lines:
            plots = []
            for chain in utils.split([i if self.values[i][key] is not None else None for i in range(len(self.values))], None):
                if chain:
                    plots.append(pg.PlotDataItem(chain, [self.values[i][key] for i in chain], pen={'color': colors[color], 'width': 2}))
                    plotItem.addItem(plots[-1])

            self.widgets.append((plotItem, plots))
            if plots:
                legend.addItem(plots[0], self.tableLabels[key])
            color += 1

        placesNum = data_parser.places_num(bars, mbars)
        if placesNum:
            bar_width = 0.9 / placesNum
            for bs, sign in [(bars, 1), (mbars, -1)]:
                for bar in bs:
                    key, place = bar
                    barGraphs = []

                    for chain in utils.split([i if self.values[i][key] is not None else None for i in range(len(self.values))], None):
                        if chain:
                            ys = [self.values[i][key] for i in chain]
                            positive = list(map(lambda x: math.copysign(1, x), ys)).count(1) > len(ys) / 2
                            if (positive and sign == -1) or (not positive and sign == 1):
                                ys = [-y for y in ys]

                            barGraphs.append(pg.BarGraphItem(x=[c + bar_width * place for c in chain], height=ys,
                                                             width=bar_width, brush=pg.mkBrush(colors[color] + (130,)), pen=pg.mkPen('k')))
                            plotItem.addItem(barGraphs[-1])

                    self.widgets.append((plotItem, barGraphs))
                    legend.addItem(ItemData('s', colors[color] + (200,)), self.tableLabels[key])
                    color += 1

        return color

    def draw_graph(self):
        pg.setConfigOption('foreground', 'w')
        plots = []
        twins = []
        legends = []

        str_dates = [date.strftime("%d/%m/%Y") for date in self.dates]

        for left, right in self.pattern:
            color = 0
            self.nextRow()
            plots.append(MyPlot(str_dates))
            self.addItem(item=plots[-1])
            legends.append(pg.LegendItem(offset=(100, 20)))
            legends[-1].setParentItem(plots[-1])

            color = self.draw_axis("left", legends[-1], plots[-1], color, *left)

            twins.append(pg.ViewBox())
            if right:
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

                self.draw_axis("right", legends[-1], twins[-1], color, *right)

        for i in range(len(plots)):
            for j in range(i + 1, len(plots)):
                plots[i].setXLink(plots[j])

        if plots:
            plots[0].setXRange(0, len(str_dates))

        vLines = []
        hLines = []
        labels = []
        for p in plots:
            vLines.append(pg.InfiniteLine(angle=90, movable=False, hoverPen=pg.mkPen('w')))
            hLines.append(pg.InfiniteLine(angle=0, movable=False, hoverPen=pg.mkPen('w')))
            labels.append(pg.TextItem(anchor=(0, 1)))
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
                if 0 <= int(x) < len(str_dates):
                    labels[i].setText(str_dates[int(x)])

        self.scene().sigMouseMoved.connect(mouseMoved)

class CheckedGraph(QtGui.QWidget):
    def __init__(self, dates, values, pattern, tableLabels, title):
        QtGui.QWidget.__init__(self)

        self.setWindowTitle(title)
        self.graph = Graph(dates, values, pattern, tableLabels)

        self.mainLayout = QtGui.QVBoxLayout(self)
        interface_common.set_title(self.mainLayout, title)
        self.graphLayout = QtGui.QHBoxLayout()
        self.mainLayout.insertLayout(1, self.graphLayout, stretch=10)

        self.choiceTree = QtGui.QTreeWidget()
        interface_common.draw_pattern(self.choiceTree, pattern, tableLabels, True)
        self.choiceTree.itemChanged.connect(self.fix)

        self.graphLayout.addWidget(self.choiceTree, stretch=1)
        self.graphLayout.addWidget(self.graph, stretch=8)

        self.showMaximized()

    def fix(self, item, i):
        self.graph.fix(int(item.toolTip(0)), item.checkState(0) == QtCore.Qt.Checked)