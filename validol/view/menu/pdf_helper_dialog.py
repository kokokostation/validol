from PyQt5.QtWidgets import QComboBox

from validol.view.utils.file_picker import FilePicker
from validol.view.utils.dialog import MyDialog


class PdfHelperDialog(MyDialog):
    def __init__(self, processors, widgets):
        self.processors = QComboBox()
        self.processors.addItems(processors)

        self.expirations_file = FilePicker('Expirations history', True)
        self.active_folder = FilePicker('Active history', False)

        MyDialog.__init__(self, [self.processors, self.expirations_file, self.active_folder] +
                          widgets)

        self.setWindowTitle("Pdf helper")

    def on_accepted(self):
        return {
            'processor': self.processors.currentText(),
            'active_folder': self.active_folder.get_path(),
            'expirations_file': self.expirations_file.get_path()
        }
