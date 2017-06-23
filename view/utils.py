from PyQt5 import QtWidgets


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



