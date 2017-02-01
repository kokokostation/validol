import sys
from PyQt5 import QtGui
from main_window import Window
from startup import init
import data_parser
import os
import utils
import datetime as dt

# init()
#
# app = QtGui.QApplication(sys.argv)
# window = Window(app)
# window.show()
# sys.exit(app.exec_())

os.chdir("data")

for code, _ in data_parser.get_platforms():
    index = data_parser.get_actives(code)
    dates = list(sorted(map(utils.parse_isoformat_date, os.listdir(code))))
    os.makedirs("/".join([code, "parsed"]))

    for date in dates:
        file = open(code + "/" + date.isoformat(), "r")
        data_parser.parse_date(code, date, file.read(), index)
        file.close()