from PyQt5.QtWidgets import QFileDialog, QWidget, QLineEdit, QPushButton, QHBoxLayout, QLabel
import os


class FilePicker(QWidget):
    def __init__(self, name, file):
        QWidget.__init__(self)

        self.file = file

        self.path = QLineEdit()
        self.path.setReadOnly(True)

        self.browse_button = QPushButton('Browse')
        self.browse_button.clicked.connect(self.browse)

        self.name = QLabel(name)

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.name, stretch=1)
        self.layout.addWidget(self.path, stretch=8)
        self.layout.addWidget(self.browse_button, stretch=1)

    def browse(self):
        if self.file:
            path, _ = QFileDialog.getOpenFileName()
        else:
            path = QFileDialog.getExistingDirectory()

        self.path.setText(path)

    def get_path(self):
        path = self.path.text()
        if path:
            return os.path.relpath(self.path.text())
        else:
            return path