from PyQt5 import QtWidgets
import json


def scrollable_area(layout):
    scroll = QtWidgets.QScrollArea()
    scroll.setWidgetResizable(True)
    inner = QtWidgets.QFrame(scroll)
    inner.setLayout(layout)
    scroll.setWidget(inner)
    return scroll


def set_title(layout, title):
    denotions = QtWidgets.QTextEdit()
    denotions.setText(title)
    denotions.setReadOnly(True)
    layout.addWidget(denotions, stretch=1)


def prettify_json(json_str):
    return json.dumps(json.loads(json_str), indent=4, sort_keys=True)


def flatten_json(json_str):
    return json.dumps(json.loads(json_str))


def display_error(title, text):
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Critical)
    msg.setText(text)
    msg.setWindowTitle(title)
    msg.exec_()


def mark(text, widget):
    layout = QtWidgets.QHBoxLayout()

    layout.addWidget(QtWidgets.QLabel(text), stretch=1)
    layout.addWidget(widget, stretch=8)

    return layout



