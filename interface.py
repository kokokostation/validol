import sys
from PyQt4 import QtGui, QtCore
import parser
# from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
# import matplotlib.pyplot as plt
# from range_slider import QRangeSlider
import pyqtgraph as pg
import math
import numpy as np

class Window(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.grabber = parser.Grabber()

        self.platforms = QtGui.QListWidget(self)
        self.platforms.itemClicked.connect(self.platform_chosen)
        for code, name in self.grabber.get_platforms():
            wi = QtGui.QListWidgetItem(name)
            wi.setToolTip(code)
            self.platforms.addItem(wi)

        self.actives = QtGui.QListWidget(self)

        self.cached_prices = QtGui.QListWidget(self)
        for url, name in self.grabber.get_cached_prices():
            wi = QtGui.QListWidgetItem(name)
            wi.setToolTip(url)
            self.cached_prices.addItem(wi)


        self.submit_active_button = QtGui.QPushButton('Submit active', self)
        self.submit_active_button.clicked.connect(self.submit_active)

        self.clear = QtGui.QPushButton('Clear', self)
        self.clear.clicked.connect(self.clear_actives)

        self.draw_table1 = QtGui.QPushButton('Draw table 1', self)
        self.draw_table1.clicked.connect(self.table1)

        self.draw_table2 = QtGui.QPushButton('Draw table 2', self)

        self.main_layout = QtGui.QVBoxLayout(self)

        self.lists_layout = QtGui.QHBoxLayout()

        self.actives_layout = QtGui.QVBoxLayout()
        self.actives_layout.addWidget(self.clear)
        self.actives_layout_widgets = []
        self.actives_layout_lines = []
        self.chosen_actives = []

        self.bottom_buttons_layout = QtGui.QHBoxLayout()

        self.lists_layout.addWidget(self.platforms)
        self.lists_layout.addWidget(self.actives)
        self.lists_layout.insertLayout(2, self.actives_layout)
        self.lists_layout.addWidget(self.cached_prices)

        self.bottom_buttons_layout.addWidget(self.submit_active_button)
        self.bottom_buttons_layout.addWidget(self.draw_table1)
        self.bottom_buttons_layout.addWidget(self.draw_table2)

        self.main_layout.insertLayout(0, self.lists_layout)
        self.main_layout.insertLayout(1, self.bottom_buttons_layout)

        self.showMaximized()

    def submit_active(self):
        self.chosen_actives.append((self.platforms.currentItem().toolTip(), self.platforms.currentItem().text(), self.actives.currentItem().text()))

        self.actives_layout_widgets.append((QtGui.QLineEdit(), QtGui.QLineEdit(), QtGui.QPushButton('Submit cached'), QtGui.QPushButton('Clear')))
        last_line_widgets = self.actives_layout_widgets[-1]

        self.actives_layout_lines.append(QtGui.QVBoxLayout())
        last_line = self.actives_layout_lines[-1]

        last_line_widgets[0].setReadOnly(True)
        last_line_widgets[0].setText(self.platforms.currentItem().text() + "/" + self.actives.currentItem().text())

        last_line_widgets[2].clicked.connect(lambda: self.submit_cached(last_line_widgets[1], self.cached_prices))
        last_line_widgets[3].clicked.connect(lambda: self.clearActive(last_line))

        for w in last_line_widgets:
            last_line.addWidget(w)

        self.actives_layout.insertLayout(len(self.actives_layout_lines) - 1, last_line)

    def submit_cached(self, lineEdit, listWidget):
        lineEdit.setText(listWidget.currentItem().toolTip())

    def platform_chosen(self):
        self.actives.clear()

        for active in self.grabber.get_actives(self.platforms.currentItem().toolTip()):
            self.actives.addItem(active)

    def clearActive(self, vbox):
        i = self.actives_layout_lines.index(vbox)
        self.removeLine(i)

    def removeLine(self, i):
        line = self.actives_layout_lines[i]

        for w in self.actives_layout_widgets[i]:
            line.removeWidget(w)
            w.hide()

        self.actives_layout.removeItem(line)

        self.actives_layout_lines.pop(i)
        self.actives_layout_widgets.pop(i)
        self.chosen_actives.pop(i)

    def clear_actives(self):
        for i in range(len(self.actives_layout_lines) - 1, -1, -1):
            self.removeLine(i)

    def table1(self):
        url_widget = self.actives_layout_widgets[0][1]
        chosen_platform, chosen_platform_name, chosen_active = self.chosen_actives[0]
        data, name, url, new = self.grabber.get_info(chosen_platform, chosen_active, parser.table1_from_fields, url_widget.text())
        if new:
            wi = QtGui.QListWidgetItem(name)
            wi.setToolTip(url)
            self.cached_prices.addItem(wi)

        title = chosen_platform_name + "/" + chosen_active + "; Price: " + name

        self.table = pg.TableWidget()
        self.table.setWindowTitle(title)
        self.table.showMaximized()

        data = np.array([tuple([d[key] for key in parser.table1_labels]) for d in data], dtype=[(key, type(data[0][key])) for key in parser.table1_labels])

        self.table.setData(data)

        colors = [(255, 0, 0), (0, 255, 255), (0, 255, 0), (255, 255, 255), (255, 255, 0), (255, 0, 255), (0, 0, 255)]
        # colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']

        self.win = pg.GraphicsWindow()
        self.win.setWindowTitle(title)

        pg.setConfigOption('foreground', 'w')
        plots = []
        twins = []
        legends = []

        xs = np.arange(len(data))
        str_dates = [d["Date"].strftime("%d/%m/%Y") for d in data]

        class MyAxisItem(pg.AxisItem):
            def tickStrings(self, values, scale, spacing):
                result = []
                for v in values:
                    if 0 <= v < len(str_dates):
                        result.append(str_dates[int(v)])
                    else:
                        result.append('')
                return result

        class MyPlot(pg.PlotItem):
            def fixAutoRange(self):
                self.enableAutoRange(y=True)

            def __init__(self, **kargs):
                pg.PlotItem.__init__(self, axisItems={'bottom': MyAxisItem(orientation='bottom')}, **kargs)

                self.vb.setAutoVisible(y=1)

                self.vb.sigRangeChangedManually.connect(self.fixAutoRange)

        class ItemData():
            def __init__(self, symbol, brush):
                self.opts = {'symbol': symbol, 'brush': brush, 'pen': None, 'size': 20}

        for i in range(len(parser.graph_info)):
            self.win.nextRow()
            plots.append(MyPlot())
            self.win.addItem(item=plots[-1])
            color = 0
            legends.append(pg.LegendItem(offset=(50, 20)))
            legends[-1].setParentItem(plots[-1])

            for key in parser.graph_info[i][0]:
                legends[-1].addItem(plots[-1].plot(xs, [d[key] for d in data], pen={'color': colors[color], 'width': 2}), key)

                color += 1

            twins.append(pg.ViewBox())
            if parser.graph_info[i][1]:
                plots[-1].showAxis('right')
                plots[-1].scene().addItem(twins[-1])
                plots[-1].getAxis('right').linkToView(twins[-1])
                twins[-1].setXLink(plots[-1])

                def updateViews():
                    for p, last_plot in zip(twins, plots):
                        p.setGeometry(last_plot.vb.sceneBoundingRect())
                        p.linkedViewChanged(last_plot.vb, p.XAxis)

                updateViews()
                plots[-1].vb.sigResized.connect(updateViews)

                bar_width = 0.9 / math.ceil(len(parser.graph_info[i][1]) / 2)

                for j in range(len(parser.graph_info[i][1])):
                    key, sign = parser.graph_info[i][1][j]
                    barGraph = pg.BarGraphItem(x=xs + bar_width * (j // 2), height=[sign * d[key] for d in data], width=bar_width, brush=pg.mkBrush(colors[color] + (130,)), pen=pg.mkPen('k'))
                    twins[-1].addItem(barGraph)
                    legends[-1].addItem(ItemData('s', colors[color] + (200,)), key)
                    color += 1

        for i in range(len(plots)):
            for j in range(i + 1, len(plots)):
                plots[i].setXLink(plots[j])

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

        self.win.scene().sigMouseMoved.connect(mouseMoved)

        self.win.showMaximized()