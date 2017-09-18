from PyQt5.QtWidgets import QComboBox, QCompleter
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QSortFilterProxyModel


class SearchableComboBox(QComboBox):
    def __init__(self, parent=None):
        QComboBox.__init__(self, parent)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setEditable(True)

        self.completer = QCompleter(self)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)

        self.p_filter_model = QSortFilterProxyModel()
        self.p_filter_model.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self.completer.setPopup(self.completer.popup())

        self.setCompleter(self.completer)

        self.lineEdit().textEdited.connect(self.p_filter_model.setFilterFixedString)

    def setModel(self, model):
        super().setModel(model)
        self.p_filter_model.setSourceModel(model)
        self.completer.setModel(self.p_filter_model)

    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.p_filter_model.setFilterKeyColumn(column)
        super().setModelColumn(column)

    def setTextIfCompleterIsClicked(self, text):
        if text:
            self.setCurrentIndex(self.findText(text))

    def setItems(self, items):
        self.clear()

        model = QStandardItemModel()

        for i, word in enumerate(items):
            item = QStandardItem(word)
            model.setItem(i, 0, item)

        self.setModel(model)
        self.setModelColumn(0)