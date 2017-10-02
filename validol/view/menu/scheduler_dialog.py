from PyQt5 import QtCore, QtWidgets, QtGui

from validol.view.view_element import ViewElement
from validol.view.utils.tipped_list import TippedList
from validol.view.utils.colorful_delegate import ColorfulDelegate


class SDTippedList(TippedList):
    def __init__(self, model_launcher):
        ro_line = QtWidgets.QLineEdit()
        ro_line.setReadOnly(True)

        self.delegate = ColorfulDelegate()

        TippedList.__init__(self, model_launcher, ro_line, QtWidgets.QListWidget())

        self.list.setItemDelegate(self.delegate)

    def get_items(self):
        schedulers = self.model_launcher.read_schedulers()
        self.delegate.set_colors(
            [QtGui.QColor(0, 255, 0) if scheduler.working else QtGui.QColor(255, 0, 0)
             for scheduler in schedulers])

        return schedulers

    def set_view(self, item):
        self.view.setText(item.cron)


class SchedulerDialog(ViewElement, QtWidgets.QWidget):
    def __init__(self, controller_launcher, model_launcher):
        QtWidgets.QWidget.__init__(self)
        ViewElement.__init__(self, controller_launcher, model_launcher)

        self.setWindowTitle('Scheduler dialog')

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.creation_layout = QtWidgets.QVBoxLayout()
        self.managing_layout = QtWidgets.QVBoxLayout()
        self.buttons_layout = QtWidgets.QHBoxLayout()

        self.schedulers = QtWidgets.QComboBox()
        update_manager = self.model_launcher.get_update_manager()
        for index, item in enumerate(update_manager.get_sources()):
            self.schedulers.addItem(item['name'])
            self.schedulers.setItemData(index, item.get('description', 'No description available'),
                                        QtCore.Qt.ToolTipRole)

        self.cron_line = QtWidgets.QLineEdit()
        self.cron_line.setPlaceholderText('Schedule in cron format')

        self.switched_on = QtWidgets.QCheckBox('Switched on by default')
        self.switched_on.setChecked(True)

        self.tipped_list = SDTippedList(self.model_launcher)

        self.switch_button = QtWidgets.QPushButton('Switch on/off')
        self.switch_button.clicked.connect(self.switch)

        self.remove_button = QtWidgets.QPushButton('Remove')
        self.remove_button.clicked.connect(self.remove)

        self.create_button = QtWidgets.QPushButton('Create scheduler')
        self.create_button.clicked.connect(self.create_scheduler)

        self.buttons_layout.addWidget(self.switch_button)
        self.buttons_layout.addWidget(self.remove_button)

        self.managing_layout.addWidget(self.tipped_list.list)
        self.managing_layout.addWidget(self.tipped_list.view)
        self.managing_layout.addLayout(self.buttons_layout)

        self.creation_layout.addWidget(self.schedulers)
        self.creation_layout.addWidget(self.cron_line)
        self.creation_layout.addWidget(self.switched_on)
        self.creation_layout.addWidget(self.create_button)

        self.main_layout.addLayout(self.managing_layout)
        self.main_layout.addLayout(self.creation_layout)

        self.show()

    def refresh(self):
        self.tipped_list.refresh()
        self.controller_launcher.refresh_schedulers()

    def create_scheduler(self):
        name = self.schedulers.currentText()
        cron = self.cron_line.text()
        working = self.switched_on.checkState() == QtCore.Qt.Checked

        self.model_launcher.write_scheduler(name, cron, working)

        self.schedulers.setCurrentIndex(0)
        self.cron_line.clear()
        self.switched_on.setChecked(True)

        self.refresh()

    def switch(self):
        self.model_launcher.switch_scheduler(self.tipped_list.current_item())
        self.refresh()

    def remove(self):
        self.model_launcher.remove_scheduler(self.tipped_list.current_item())
        self.refresh()

