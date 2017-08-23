from PyQt5.QtWidgets import QLineEdit

from validol.view.utils.dialog import MyDialog


class GluedActiveDialog(MyDialog):
    def __init__(self):
        self.name = QLineEdit()
        self.name.setPlaceholderText('Active name')

        MyDialog.__init__(self, [self.name])

        self.setWindowTitle("Glued active")

    def on_accepted(self):
        return self.name.text()
