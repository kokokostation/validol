from PyQt5 import QtWidgets
from collections import OrderedDict


class TippedList:
    def __init__(self, model_launcher, view, list_widget):
        self.model_launcher = model_launcher
        self.list = list_widget
        self.view = view

        self.list.currentItemChanged.connect(self.item_chosen)

        self.refresh()

    def item_chosen(self):
        item = self.current_item()
        if item is not None:
            self.view.clear()
            self.set_view(item)

    def refresh(self):
        self.list.clear()
        self.view.clear()
        self.items = self.get_items()

        for item in self.items:
            wi = QtWidgets.QListWidgetItem(item.name)
            wi.setData(4, item)
            self.list.addItem(wi)

        self.list.setCurrentRow(self.list.count() - 1)

    def current_item(self):
        if self.list.currentItem() is None:
            return None
        else:
            return self.list.currentItem().data(4)

    def set_view(self, item):
        raise NotImplementedError

    def get_items(self):
        raise NotImplementedError


class TextTippedList(TippedList):
    def __init__(self, model_launcher, list_widget):
        ro_text_edit = QtWidgets.QTextEdit()
        ro_text_edit.setReadOnly(True)

        TippedList.__init__(self, model_launcher, ro_text_edit, list_widget)