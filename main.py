import sys
from PyQt5 import QtGui
from interface import Window
from downloader import init

init()

app = QtGui.QApplication(sys.argv)
window = Window(app)
window.show()
sys.exit(app.exec_())