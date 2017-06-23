from PyQt5 import QtCore


class ButtonGroup():
    def __init__(self):
        self.buttons = []
        self.last = None

    def add_item(self, button):
        button.stateChanged.connect(lambda: self.state_changed(button))
        self.buttons.append(button)

    def id(self, button):
        return self.buttons.index(button)

    def state_changed(self, button):
        if self.last and self.last != button:
            self.last.setChecked(False)

        self.last = button

    def checked_button(self):
        if self.last and self.last.checkState() == QtCore.Qt.Checked:
            return self.buttons.index(self.last), self.last.text()