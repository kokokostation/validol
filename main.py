import sys
from PyQt4 import QtGui, QtCore
from interface import Window
from downloader import update

update()

app = QtGui.QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec_())