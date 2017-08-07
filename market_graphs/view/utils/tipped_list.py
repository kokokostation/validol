from PyQt5 import QtWidgets

class TippedList:
    def __init__(self, items_getter, view_setter, view):
        self.items_getter = items_getter
        self.view_setter = view_setter

        self.list = QtWidgets.QListWidget()
        self.view = view

        self.list.currentItemChanged.connect(self.item_chosen)

        self.refresh()

    def item_chosen(self):
        if self.items:
            item = self.items[self.list.currentRow()]
            self.view.clear()
            self.view_setter(self.view, item)

    def refresh(self):
        self.list.clear()
        self.view.clear()
        self.items = self.items_getter()

        for item in self.items:
            wi = QtWidgets.QListWidgetItem(item.name)
            self.list.addItem(wi)

        self.list.setCurrentRow(self.list.count() - 1)

    def current_item(self):
        return self.items[self.list.currentRow()]