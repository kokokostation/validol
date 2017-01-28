import sys
from PyQt4 import QtGui, QtCore
from interface import Window
from downloader import init

init()

app = QtGui.QApplication(sys.argv)
window = Window(app)
window.show()
sys.exit(app.exec_())