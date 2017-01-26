import math
import pyqtgraph as pg
import numpy as np

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

def draw_graph(contents, title):
    win = pg.GraphicsWindow()
    win.setWindowTitle(title)

    pg.setConfigOption('foreground', 'w')
    plots = []
    twins = []
    legends = []

    for data, scheme in contents:
        xs = np.arange(len(data))
        str_dates = [d["Date"].strftime("%d/%m/%Y") for d in data]
        
        for i in range(len(scheme)):
            win.nextRow()
            plots.append(MyPlot(str_dates))
            win.addItem(item=plots[-1])
            color = 0
            legends.append(pg.LegendItem(offset=(50, 20)))
            legends[-1].setParentItem(plots[-1])
        
            for key in scheme[i][0]:
                legends[-1].addItem(plots[-1].plot(xs, [d[key] for d in data], pen={'color': colors[color], 'width': 2}), key)
        
                color += 1
        
            twins.append(pg.ViewBox())
            if scheme[i][1]:
                plots[-1].showAxis('right')
                plots[-1].scene().addItem(twins[-1])
                plots[-1].getAxis('right').linkToView(twins[-1])
                twins[-1].setXLink(plots[-1])

                #сделать нормально
                def updateViews():
                    for p, last_plot in zip(twins, plots):
                        p.setGeometry(last_plot.vb.sceneBoundingRect())
                        p.linkedViewChanged(last_plot.vb, p.XAxis)
        
                updateViews()
                plots[-1].vb.sigResized.connect(updateViews)
        
                bar_width = 0.9 / math.ceil(len(scheme[i][1]) / 2)
        
                for j in range(len(scheme[i][1])):
                    key, sign = scheme[i][1][j]
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

    win.scene().sigMouseMoved.connect(mouseMoved)

    win.showMaximized()

    return win