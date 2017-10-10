from PyQt5.QtWidgets import QTextEdit

from validol.view.utils.dialog import MyDialog
from validol.view.utils.utils import prettify_json, flatten_json, display_error


class PatternEditDialog(MyDialog):
    def __init__(self, json_str):
        self.flattened_json = None

        self.edit = QTextEdit()
        self.edit.setText(prettify_json(json_str))

        MyDialog.__init__(self, [self.edit], False)

        self.setWindowTitle("Pattern edit")

        self.showMaximized()

    def can_accept(self):
        try:
            self.flattened_json = flatten_json(self.edit.toPlainText())
            return True
        except ValueError as ve:
            display_error('JSON parsing error, details: ', str(ve))
            return False

    def on_accepted(self):
        return self.flattened_json
