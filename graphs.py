from PyQt4 import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
import utils

colors = [(255, 0, 0), (0, 255, 255), (0, 255, 0), (255, 255, 255), (255, 255, 0), (255, 0, 255), (0, 0, 255)]
# colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']

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
    def __init__(self, data, pattern):
        pg.GraphicsWindow.__init__(self)

        self.widgets = []
        self.pattern = utils.flatten(pattern)

        self.draw_graph(data, pattern)

    def fix(self, label, toDo):
        plotItem, plots = self.widgets[self.pattern.index(label)]

        for plot in plots:
            if toDo == True:
                plotItem.addItem(plot)
            else:
                plotItem.removeItem(plot)

    def draw_axis(self, label, legend, plotItem, data, color, lines, bars, mbars):
        legend.addItem(ItemData(None, None), label)

        #code duplication
        for key in lines:
            plots = []

            for chain in utils.split([i if key in data[i] else None for i in range(len(data))], None):
                if chain:
                    plots.append(pg.PlotDataItem(chain, [data[i][key] for i in chain], pen={'color': colors[color], 'width': 2}))
                    plotItem.addItem(plots[-1])

            self.widgets.append((plotItem, plots))
            if plots:
                legend.addItem(plots[0], key)
            color += 1

        if bars or mbars:
            bar_width = 0.9 / max(len(bars), len(mbars))
            #sequence of bars
            for bs, sign in [(bars, 1), (mbars, -1)]:
                for i in range(len(bs)):
                    key = bs[i]
                    barGraphs = []

                    for chain in utils.split([i if key in data[i] else None for i in range(len(data))], None):
                        if chain:
                            barGraphs.append(pg.BarGraphItem(x=[c + bar_width * i for c in chain], height=[sign * data[i][key] for i in chain],
                                                             width=bar_width, brush=pg.mkBrush(colors[color] + (130,)), pen=pg.mkPen('k')))
                            plotItem.addItem(barGraphs[-1])

                    self.widgets.append((plotItem, barGraphs))
                    legend.addItem(ItemData('s', colors[color] + (200,)), key)
                    color += 1

        return color

    def draw_graph(self, data, pattern):
        pg.setConfigOption('foreground', 'w')
        plots = []
        twins = []
        legends = []

        str_dates = [d["Date"].strftime("%d/%m/%Y") for d in data]

        for left, right in pattern:
            color = 0
            self.nextRow()
            plots.append(MyPlot(str_dates))
            self.addItem(item=plots[-1])
            legends.append(pg.LegendItem(offset=(50, 20)))
            legends[-1].setParentItem(plots[-1])

            color = self.draw_axis("left", legends[-1], plots[-1], data, color, *left)

            twins.append(pg.ViewBox())
            if right:
                plots[-1].showAxis('right')
                plots[-1].scene().addItem(twins[-1])
                plots[-1].getAxis('right').linkToView(twins[-1])
                twins[-1].setXLink(plots[-1])
                twins[-1].setAutoVisible(y=1)

                #сделать нормально
                def updateViews():
                    for p, last_plot in zip(twins, plots):
                        p.enableAutoRange(y=True)
                        p.setGeometry(last_plot.vb.sceneBoundingRect())
                        p.linkedViewChanged(last_plot.vb, p.XAxis)

                updateViews()
                plots[-1].vb.sigResized.connect(updateViews)

                self.draw_axis("right", legends[-1], twins[-1], data, color, *right)

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
    def __init__(self, data, pattern, title):
        QtGui.QWidget.__init__(self)

        self.setWindowTitle(title)
        self.pattern = pattern
        self.graph = Graph(data, pattern)

        self.mainLayout = QtGui.QHBoxLayout(self)

        self.choiceTree = QtGui.QTreeWidget()
        for i in range(len(self.pattern)):
            root = QtGui.QTreeWidgetItem([str(i)])
            children = [QtGui.QTreeWidgetItem([label]) for label in ["left", "right"]]

            for j in range(2):
                types = [QtGui.QTreeWidgetItem([label]) for label in ["line", "bar", "-bar"]]
                for k in range(3):
                    for label in self.pattern[i][j][k]:
                        item = QtGui.QTreeWidgetItem([label])
                        item.setCheckState(0, QtCore.Qt.Checked)
                        item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                        types[k].addChild(item)
                    children[j].addChild(types[k])
                root.addChild(children[j])

            self.choiceTree.addTopLevelItem(root)

            root.setExpanded(True)
            for i in range(root.childCount()):
                root.child(i).setExpanded(True)
                for j in range(root.child(i).childCount()):
                    root.child(i).child(j).setExpanded(True)
        self.choiceTree.itemChanged.connect(self.fix)

        self.mainLayout.addWidget(self.choiceTree, stretch=1)
        self.mainLayout.addWidget(self.graph, stretch=8)

        self.showMaximized()

    def fix(self, item, i):
        self.graph.fix(item.text(0), item.checkState(0) == QtCore.Qt.Checked)