from PyQt5 import QtCore, QtWidgets
from market_graphs.model.store.miners.flavors import GLUED_ACTIVE

from market_graphs.view.utils.utils import scrollable_area
from market_graphs.view.utils.tipped_list import TippedList
from market_graphs.view.view_element import ViewElement


class Window(ViewElement, QtWidgets.QWidget):
    def __init__(self, app, controller_launcher, model_launcher):
        QtWidgets.QWidget.__init__(self)
        ViewElement.__init__(self, controller_launcher, model_launcher)

        self.app = app

        self.setWindowTitle("COTs")

        self.searchResult = None

        self.actives = QtWidgets.QListWidget()
        self.actives.itemDoubleClicked.connect(self.submit_active)
        self.searchLine = QtWidgets.QLineEdit()
        self.searchLine.setPlaceholderText("Search")
        self.searchLine.textChanged.connect(self.search)
        self.searchLine.returnPressed.connect(self.search)
        self.activesListLayout = QtWidgets.QVBoxLayout()
        self.activesListLayout.addWidget(self.searchLine)
        self.activesListLayout.addWidget(self.actives)

        self.platforms = QtWidgets.QListWidget()
        self.platforms.currentItemChanged.connect(self.platform_chosen)

        self.flavors = QtWidgets.QListWidget()
        self.flavors.currentItemChanged.connect(self.flavor_chosen)

        for flavor in self.model_launcher.get_flavors():
            self.flavors.addItem(flavor["name"])

        self.flavors.setCurrentRow(0)

        self.drawTable = QtWidgets.QPushButton('Draw table')
        self.drawTable.clicked.connect(self.draw_table)

        self.clear = QtWidgets.QPushButton('Clear all')
        self.clear.clicked.connect(self.clear_actives)

        self.createTable = QtWidgets.QPushButton('Create table')
        self.createTable.clicked.connect(self.create_table)

        self.updateButton = QtWidgets.QPushButton('Update')
        self.updateButton.clicked.connect(self.on_update)

        self.removeTable = QtWidgets.QPushButton('Remove table')
        self.removeTable.clicked.connect(self.remove_table)

        self.leftLayout = QtWidgets.QVBoxLayout()
        self.leftLayout.addWidget(self.flavors)
        self.leftLayout.addWidget(self.updateButton)

        self.cached_prices = QtWidgets.QListWidget()
        self.set_cached_prices()

        def view_setter(view, table_pattern):
            view.setText(str(table_pattern))

        ro_text_edit = QtWidgets.QTextEdit()
        ro_text_edit.setReadOnly(True)

        self.tipped_list = TippedList(lambda: model_launcher.get_tables(),
                                      view_setter, ro_text_edit)

        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.lists_layout = QtWidgets.QHBoxLayout()

        self.glue_layout = QtWidgets.QVBoxLayout()
        self.glue_name = QtWidgets.QLineEdit()
        self.glue_button = QtWidgets.QPushButton('Glue actives')
        self.glue_button.clicked.connect(self.glue)
        self.remove_glue = QtWidgets.QPushButton('Remove glued active')
        self.remove_glue.clicked.connect(self.remove_glued_active)

        self.rightLayout = QtWidgets.QVBoxLayout()
        self.rightLayout.addWidget(self.cached_prices)
        self.rightLayout.addWidget(self.tipped_list.list)
        self.rightLayout.addWidget(self.removeTable)
        self.rightLayout.addWidget(self.remove_glue)
        self.rightLayout.addWidget(self.tipped_list.view)
        self.rightLayout.addWidget(self.createTable)

        self.actives_layout = QtWidgets.QVBoxLayout()
        self.actives_layout_widgets = []
        self.actives_layout_lines = []
        self.chosen_actives = []

        self.actives_layout.addWidget(self.clear, alignment=QtCore.Qt.AlignTop)
        self.actives_layout.addWidget(self.glue_name, alignment=QtCore.Qt.AlignBottom)
        self.actives_layout.addWidget(self.glue_button)

        self.lists_layout.insertLayout(0, self.leftLayout)
        self.lists_layout.addWidget(self.platforms)
        self.lists_layout.insertLayout(2, self.activesListLayout)
        self.lists_layout.addWidget(scrollable_area(self.actives_layout))
        self.lists_layout.insertLayout(4, self.rightLayout)

        self.main_layout.insertLayout(0, self.lists_layout)
        self.main_layout.addWidget(self.drawTable)

        self.tables = []
        self.graphs = []
        self.tableDialogs = []

        self.showMaximized()

    def glue(self):
        if self.glue_name.text():
            self.model_launcher.write_glued_active(self.glue_name.text(), self.chosen_actives)
            self.glue_name.clear()

            self.platform_chosen()

    def remove_glued_active(self):
        active = self.actives.currentItem()
        if self.current_flavor() == GLUED_ACTIVE["name"] and active is not None:
            self.model_launcher.remove_glued_active(active.text())

            self.platform_chosen()

    def remove_table(self):
        self.model_launcher.remove_table(self.tipped_list.list.currentItem().text())
        self.tipped_list.refresh()

    def closeEvent(self, _):
        for graph in self.graphs:
            graph.close()

        for table in self.tables:
            table.close()

        for tableDialog in self.tableDialogs:
            tableDialog.close()

    def search(self):
        searchText = self.searchLine.text()
        if (self.searchResult and self.searchResult[0] != searchText) or not self.searchResult:
            self.searchResult = [searchText, self.actives.findItems(
                self.searchLine.text(), QtCore.Qt.MatchContains), 0]

        _, items, index = self.searchResult
        if items:
            self.actives.setCurrentItem(items[index % len(items)])
            self.searchResult[2] += 1

    def set_cached_prices(self):
        self.cached_prices.clear()

        for index, value in self.model_launcher.get_cached_prices().iterrows():
            wi = QtWidgets.QListWidgetItem(value["name"])
            wi.setToolTip(value["url"])
            self.cached_prices.addItem(wi)

    def submit_active(self):
        self.chosen_actives.append([self.current_flavor(),
                                    self.platforms.currentItem().toolTip(),
                                    self.actives.currentItem().text()])

        self.actives_layout_widgets.append((QtWidgets.QLineEdit(),
                                            QtWidgets.QLineEdit(),
                                            QtWidgets.QPushButton('Submit cached'),
                                            QtWidgets.QPushButton('Clear')))
        last_line_widgets = self.actives_layout_widgets[-1]

        self.actives_layout_lines.append(QtWidgets.QVBoxLayout())
        last_line = self.actives_layout_lines[-1]

        last_line_widgets[0].setReadOnly(True)
        last_line_widgets[0].setText(
            self.platforms.currentItem().text() + "/" + self.actives.currentItem().text())

        last_line_widgets[2].clicked.connect(
            lambda: self.submit_cached(last_line_widgets[1], self.cached_prices))
        last_line_widgets[3].clicked.connect(
            lambda: self.clear_active(last_line))

        for w in last_line_widgets:
            last_line.addWidget(w)

        self.actives_layout.insertLayout(
            len(self.actives_layout_lines), last_line)

    def submit_cached(self, lineEdit, listWidget):
        lineEdit.setText(listWidget.currentItem().toolTip())

    def current_flavor(self):
        return self.flavors.currentItem().text()

    def flavor_chosen(self):
        self.platforms.clear()

        platforms = [value for index, value in
                     self.model_launcher.get_platforms(self.current_flavor()).iterrows()]
        for platform in sorted(platforms, key=lambda x: x.PlatformName):
            wi = QtWidgets.QListWidgetItem(platform.PlatformName)
            wi.setToolTip(platform.PlatformCode)
            self.platforms.addItem(wi)

        self.platforms.setCurrentRow(0)

    def platform_chosen(self):
        if self.platforms.currentItem() is None:
            return

        self.actives.clear()

        for _, active in self.model_launcher.get_actives(self.platforms.currentItem().toolTip(),
                                                      self.current_flavor()).iterrows():
            self.actives.addItem(active.ActiveName)

    def clear_active(self, vbox):
        i = self.actives_layout_lines.index(vbox)
        self.remove_line(i)

    def remove_line(self, i):
        line = self.actives_layout_lines[i]

        for w in self.actives_layout_widgets[i]:
            line.removeWidget(w)
            w.hide()

        self.actives_layout.removeItem(line)

        self.actives_layout_lines.pop(i)
        self.actives_layout_widgets.pop(i)
        self.chosen_actives.pop(i)

    def clear_actives(self):
        for i in range(len(self.actives_layout_lines) - 1, -1, -1):
            self.remove_line(i)

    def draw_table(self):
        table_pattern = self.tipped_list.current_item()
        prices_info = [bunch[1].text() for bunch in self.actives_layout_widgets]
        self.controller_launcher.draw_table(table_pattern, self.chosen_actives, prices_info)

    def create_table(self):
        self.controller_launcher.show_table_dialog()

    def on_update(self):
        self.updateButton.setText("Wait a sec. Updating the data...")
        self.app.processEvents()
        if not self.controller_launcher.update_data():
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Unable to update due to network error")
            msg.setWindowTitle("Network error")
            msg.exec_()
        self.updateButton.setText("Update")
