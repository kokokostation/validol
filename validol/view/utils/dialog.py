from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt


class MyDialog(QDialog):
    def __init__(self, widgets):
        QDialog.__init__(self, flags=Qt.Window)

        self.setModal(True)

        self.main_layout = QVBoxLayout(self)

        for wi in widgets:
            self.main_layout.addWidget(wi)

        self.ready_button = QPushButton('Ready')
        self.ready_button.clicked.connect(lambda: self.accept())

        self.main_layout.addWidget(self.ready_button)

    def get_data(self):
        if self.exec_() == QDialog.Accepted:
            return self.on_accepted()
        else:
            return None

    def on_accepted(self):
        raise NotImplementedError