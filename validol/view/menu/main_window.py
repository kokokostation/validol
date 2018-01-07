from PyQt5 import QtWidgets
from collections import OrderedDict
from functools import partial, wraps

from validol.view.utils.tipped_list import TextTippedList
from validol.view.utils.utils import scrollable_area
from validol.view.view_element import ViewElement
from validol.view.utils.searchable_list import SearchableList
from validol.model.store.view.active_info import ActiveInfo


class MWTippedList(TextTippedList):
    def set_view(self, item):
        self.view.setText(str(item))

    def get_items(self):
        return self.model_launcher.get_tables()


def with_ai(f):
    @wraps(f)
    def wrapped(self):
        ai = self.active_info()

        if ai is not None:
            return f(self, ai)

    return wrapped


class Window(ViewElement, QtWidgets.QWidget):
    def __init__(self, app, controller_launcher, model_launcher):
        QtWidgets.QWidget.__init__(self)
        ViewElement.__init__(self, controller_launcher, model_launcher)

        self.app = app

        config = self.controller_launcher.get_package_config()
        self.setWindowTitle("{name} {version}".format(**config))

        self.actives = QtWidgets.QListWidget()
        self.actives.itemDoubleClicked.connect(self.submit_active)
        self.actives.currentItemChanged.connect(self.active_chosen)

        self.searchable_list = SearchableList(self.actives)

        self.new_active_button = QtWidgets.QPushButton('New active')
        self.new_active_button.clicked.connect(self.new_active)

        self.activesListLayout = QtWidgets.QVBoxLayout()
        self.activesListLayout.addWidget(self.searchable_list.searchbar)
        self.activesListLayout.addWidget(self.actives)
        self.activesListLayout.addWidget(self.new_active_button)

        self.platforms = QtWidgets.QListWidget()
        self.platforms.currentItemChanged.connect(self.platform_chosen)

        self.active_flavors = QtWidgets.QListWidget()
        self.active_flavors.itemDoubleClicked.connect(self.submit_active)

        self.flavors = QtWidgets.QListWidget()
        self.flavors.currentItemChanged.connect(self.flavor_chosen)

        self.flavors_map = OrderedDict((flavor.name(), flavor)
                                       for flavor in self.model_launcher.get_flavors())

        for flavor in self.flavors_map.keys():
            self.flavors.addItem(flavor)

        self.flavors.setCurrentRow(0)

        self.drawTable = QtWidgets.QPushButton('Draw table')
        self.drawTable.clicked.connect(self.draw_table)

        self.update_app_button = QtWidgets.QPushButton('UPDATE APP')
        self.update_app_button.setStyleSheet("background-color: red")
        self.update_app_button.clicked.connect(self.controller_launcher.pip_update)
        self.update_app_button.hide()

        self.update_missed_schedulers_button = QtWidgets.QPushButton('Update missed schedulers')
        self.update_missed_schedulers_button.setStyleSheet("background-color: green")
        self.update_missed_schedulers_button.clicked.connect(
            self.on_update(self.controller_launcher.update_missed_schedulers, self.update_missed_schedulers_button))
        self.update_missed_schedulers_button.hide()

        self.clear = QtWidgets.QPushButton('Clear all')
        self.clear.clicked.connect(self.clear_actives)

        self.createTable = QtWidgets.QPushButton('Create table')
        self.createTable.clicked.connect(self.create_table)

        self.updateButton = QtWidgets.QPushButton('Update')
        self.updateButton.clicked.connect(
            self.on_update(self.model_launcher.update_weekly, self.updateButton))

        self.update_daily_button = QtWidgets.QPushButton('Update daily')
        self.update_daily_button.clicked.connect(
            self.on_update(self.model_launcher.update_daily, self.update_daily_button))

        self.create_scheduler_button = QtWidgets.QPushButton('Create scheduler')
        self.create_scheduler_button.clicked.connect(self.controller_launcher.show_scheduler_dialog)

        self.removeTable = QtWidgets.QPushButton('Remove table')
        self.removeTable.clicked.connect(self.remove_table)

        self.leftLayout = QtWidgets.QVBoxLayout()
        self.leftLayout.addWidget(self.flavors)
        self.leftLayout.addWidget(self.active_flavors)
        self.leftLayout.addWidget(self.update_missed_schedulers_button)
        self.leftLayout.addWidget(self.updateButton)
        self.leftLayout.addWidget(self.update_daily_button)
        self.leftLayout.addWidget(self.create_scheduler_button)

        self.cached_prices = QtWidgets.QListWidget()
        self.set_cached_prices()

        self.tipped_list = MWTippedList(self.model_launcher, QtWidgets.QListWidget())

        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.lists_layout = QtWidgets.QHBoxLayout()

        self.remove_active_button = QtWidgets.QPushButton('Remove active')
        self.remove_active_button.clicked.connect(self.remove_active)

        self.remove_active_data_button = QtWidgets.QPushButton('Remove active data')
        self.remove_active_data_button.clicked.connect(self.remove_active_data)

        self.reload_expirations_button = QtWidgets.QPushButton('Reload expirations')
        self.reload_expirations_button.clicked.connect(self.reload_expirations)

        self.rightLayout = QtWidgets.QVBoxLayout()
        self.rightLayout.addWidget(self.cached_prices)
        self.rightLayout.addWidget(self.remove_active_button)
        self.rightLayout.addWidget(self.remove_active_data_button)
        self.rightLayout.addWidget(self.reload_expirations_button)
        self.rightLayout.addWidget(self.tipped_list.list)
        self.rightLayout.addWidget(self.removeTable)
        self.rightLayout.addWidget(self.tipped_list.view)
        self.rightLayout.addWidget(self.createTable)

        self.actives_layout = QtWidgets.QVBoxLayout()

        self.actives_layout_widgets = []
        self.actives_layout_lines = []
        self.chosen_actives = []

        self.actives_layout.addWidget(self.clear)

        self.lists_layout.insertLayout(0, self.leftLayout)
        self.lists_layout.addWidget(self.platforms)
        self.lists_layout.insertLayout(2, self.activesListLayout)
        self.lists_layout.addWidget(scrollable_area(self.actives_layout))
        self.lists_layout.insertLayout(4, self.rightLayout)

        self.main_layout.addWidget(self.update_app_button)
        self.main_layout.insertLayout(1, self.lists_layout)
        self.main_layout.addWidget(self.drawTable)

        self.showMaximized()

    def current_platform_active(self):
        platform, active = self.current_platform(), self.current_active()

        if platform is None or active is None:
            return None
        else:
            return platform, active

    def active_info(self):
        pa = self.current_platform_active()

        if pa is not None:
            return ActiveInfo(self.current_flavor(), pa[0], pa[1], self.current_active_flavor())

    def current_flavor(self):
        return self.flavors_map[self.flavors.currentItem().text()]

    def current_platform(self):
        item = self.platforms.currentItem()

        if item is not None:
            return item.toolTip()

    def current_active(self):
        item = self.actives.currentItem()
        if item is not None:
            return item.text()

    def current_active_flavor(self):
        item = self.active_flavors.currentItem()
        if item is not None:
            return item.text()

    def current_price(self):
        item = self.cached_prices.currentItem()
        if item is not None:
            return item.toolTip()

    def new_active(self):
        platform = self.current_platform()

        if platform is None:
            return

        self.current_flavor().new_active(platform, self.model_launcher)

        self.platform_chosen()

    def active_chosen(self):
        pa = self.current_platform_active()

        if pa is None:
            return

        self.active_flavors.clear()

        active_flavors = self.current_flavor().active_flavors(pa[0], pa[1], self.model_launcher)

        for active_flavor in active_flavors.active_flavor:
            self.active_flavors.addItem(active_flavor)

        if not active_flavors.empty:
            self.active_flavors.setCurrentRow(0)

    @with_ai
    def remove_active(self, ai):
        self.current_flavor().remove_active(ai, self.model_launcher)

        self.platform_chosen()

    @with_ai
    def remove_active_data(self, ai):
        self.current_flavor().remove_active_data(ai, self.model_launcher)

        self.active_chosen()

    @with_ai
    def reload_expirations(self, ai):
        self.current_flavor().reload_expirations(ai, self.model_launcher)

    def remove_table(self):
        item = self.tipped_list.current_item()

        if item is not None:
            self.model_launcher.remove_table(item.name)
            self.tipped_list.refresh()

    def set_cached_prices(self):
        self.cached_prices.clear()

        for index, value in self.model_launcher.get_cached_prices().iterrows():
            wi = QtWidgets.QListWidgetItem(value["name"])
            wi.setToolTip(value["url"])
            self.cached_prices.addItem(wi)

    def submit_active(self):
        curr_ai = self.active_info()

        if curr_ai is None:
            return

        actives = curr_ai.flavor.active_infos(curr_ai, self.model_launcher)

        self.chosen_actives.extend(actives)

        for active in actives:
            active_name = QtWidgets.QLineEdit(active.flavor.show_ai(active, self.model_launcher))
            active_name.setReadOnly(True)

            price_url = QtWidgets.QLineEdit(active.price_url or '')
            submit_cached = QtWidgets.QPushButton('Submit cached')
            clear = QtWidgets.QPushButton('Clear')

            layout = QtWidgets.QVBoxLayout()

            price_url.textChanged.connect(partial(self.insert_url, active))
            submit_cached.clicked.connect(partial(self.submit_cached, price_url))
            clear.clicked.connect(partial(self.clear_active, layout))

            self.actives_layout_widgets.append((active_name, price_url, submit_cached, clear))

            for w in self.actives_layout_widgets[-1]:
                layout.addWidget(w)

            self.actives_layout_lines.append(layout)

            self.actives_layout.insertLayout(len(self.actives_layout_lines), layout)

    def insert_url(self, active, text):
        active.price_url = text

    def submit_cached(self, price_url):
        url = self.current_price()

        if url is not None:
            price_url.setText(url)

    def flavor_chosen(self):
        self.platforms.clear()

        platforms = [value for index, value in
                     self.current_flavor().platforms(self.model_launcher).iterrows()]
        for platform in sorted(platforms, key=lambda x: x.PlatformName):
            wi = QtWidgets.QListWidgetItem(platform.PlatformName)
            wi.setToolTip(platform.PlatformCode)
            self.platforms.addItem(wi)

        if self.platforms.count() > 0:
            self.platforms.setCurrentRow(0)
        else:
            self.platform_chosen()

    def platform_chosen(self):
        self.actives.clear()
        self.active_flavors.clear()

        platform = self.current_platform()

        if platform is None:
            return

        actives = self.current_flavor().actives(platform, self.model_launcher)

        for _, active in actives.iterrows():
            wi = QtWidgets.QListWidgetItem(active.ActiveName)
            self.actives.addItem(wi)

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
        while self.actives_layout_lines:
            self.remove_line(0)

    def draw_table(self):
        table_pattern = self.tipped_list.current_item()
        if table_pattern is not None:
            self.controller_launcher.draw_table(table_pattern, self.chosen_actives)

    def create_table(self):
        self.controller_launcher.show_table_dialog()

    def on_update(self, action, button):
        def shot():
            text = button.text()
            button.setText("Wait a sec. Updating the data...")
            self.app.processEvents()

            results = action()

            self.controller_launcher.notify_update(results)

            button.setText(text)

            self.active_chosen()

        return shot

    def closeEvent(self, qce):
        self.controller_launcher.on_main_window_close()

    def show_update_app_button(self):
        self.update_app_button.show()

    def show_update_missed_schedulers_button(self, needed):
        if needed:
            self.update_missed_schedulers_button.show()
        else:
            self.update_missed_schedulers_button.hide()
