import sys
from PyQt5 import QtGui
from main_window import Window
from startup import init
from update import update_sources

update_sources()

init()

# app = QtGui.QApplication(sys.argv)
# window = Window(app)
# window.show()
# sys.exit(app.exec_())

from data_parser import reparse

reparse()