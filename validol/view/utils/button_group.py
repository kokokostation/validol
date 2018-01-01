from PyQt5 import QtCore
from functools import partial


class ButtonGroup:
    def __init__(self, buttons):
        self.buttons = buttons
        for button in self.buttons:
            button.stateChanged.connect(partial(self.state_changed, button))

        self.last = None

    def id(self, button):
        return self.buttons.index(button)

    def state_changed(self, button):
        if self.last and self.last is not button:
            self.last.setChecked(False)

        self.last = button

    def clear(self):
        for button in self.buttons:
            button.setChecked(False)

    def checked_button(self):
        if self.last and self.last.checkState() == QtCore.Qt.Checked:
            return self.buttons.index(self.last), self.last.text()