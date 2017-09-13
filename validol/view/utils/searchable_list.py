from PyQt5 import QtWidgets


class SearchableList:
    def __init__(self, list_widget):
        self.searchbar = QtWidgets.QLineEdit()
        self.searchbar.setPlaceholderText("Search")
        self.searchbar.textChanged.connect(self.search)

        self.list = list_widget

    def search(self):
        for row in range(self.list.count()):
            item = self.list.item(row)
            item.setHidden(self.searchbar.text().upper() not in item.text().upper())

    def update(self):
        pass
