from PyQt5 import QtWidgets


class SearchableList:
    def __init__(self, list_widget):
        self.searchbar = QtWidgets.QLineEdit()
        self.searchbar.setPlaceholderText("Search")
        self.searchbar.textChanged.connect(self.search)

        self.list = list_widget
        self.items = []

    def update(self):
        self.items = [self.list.item(row).text() for row in range(self.list.count())]

    def search(self):
        self.list.clear()
        self.list.addItems(
            [item for item in self.items if self.searchbar.text().upper() in item.upper()])
