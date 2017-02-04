import sys
from PyQt5 import QtGui
from main_window import Window
from startup import init
import data_parser
import os
import utils
import datetime as dt

init()

app = QtGui.QApplication(sys.argv)
window = Window(app)
window.show()
sys.exit(app.exec_())