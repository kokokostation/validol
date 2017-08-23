from PyQt5.QtWidgets import QTextEdit

from validol.view.utils.dialog import MyDialog
from validol.view.utils.utils import prettify_json, flatten_json, display_error


class PatternEditDialog(MyDialog):
    def __init__(self, json_str):
        self.edit = QTextEdit()
        self.edit.setText(prettify_json(json_str))

        MyDialog.__init__(self, [self.edit])

        self.setWindowTitle("Pattern edit")


    def on_accepted(self):
        try:
            return flatten_json(self.edit.toPlainText())
        except ValueError as ve:
            display_error('JSON parsing error, details: ', str(ve))
