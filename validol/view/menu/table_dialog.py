from PyQt5 import QtWidgets, QtGui
from pyparsing import alphas, ParseException

from validol.view.view_element import ViewElement
from validol.model.resource_manager.atom_flavors import FormulaAtom
from validol.view.utils.searchable_list import SearchableList
from validol.view.utils.tipped_list import TextTippedList
from validol.view.utils.utils import display_error
from validol.model.store.structures.structure import PieceNameError


class TDTippedList(TextTippedList):
    def __init__(self, model_launcher, searchable_list):
        self.searchable_list = searchable_list

        TextTippedList.__init__(self, model_launcher, searchable_list.list)

    def get_items(self):
        return self.model_launcher.get_atoms()

    def set_view(self, atom):
        self.view.setText("{}: {}".format(atom, atom.description))


class TableDialog(ViewElement, QtWidgets.QWidget):
    def __init__(self, flags, controller_launcher, model_launcher):
        QtWidgets.QWidget.__init__(self, flags=flags)
        ViewElement.__init__(self, controller_launcher, model_launcher)

        self.setWindowTitle("Table edit")

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.boxesLayout = QtWidgets.QHBoxLayout()
        self.buttonsLayout = QtWidgets.QHBoxLayout()
        self.editLayout = QtWidgets.QVBoxLayout()
        self.leftLayout = QtWidgets.QVBoxLayout()

        self.searchable_list = SearchableList(QtWidgets.QListWidget())

        self.tipped_list = TDTippedList(self.model_launcher, self.searchable_list)
        self.tipped_list.list.itemDoubleClicked.connect(self.insert_atom)

        self.name = QtWidgets.QLineEdit()
        self.name.setPlaceholderText("Name")
        self.mainEdit = QtWidgets.QTextEdit()

        self.mode = QtWidgets.QButtonGroup()
        checkBoxes = []
        for label in ["Table", "Atom"]:
            checkBoxes.append(QtWidgets.QCheckBox(label))
            self.mode.addButton(checkBoxes[-1])
        checkBoxes[0].setChecked(True)

        self.letters = QtWidgets.QComboBox()
        self.letters.addItem("")
        for a in alphas[:10]:
            self.letters.addItem(a)
        self.letters.setCurrentIndex(1)

        self.leftLayout.addWidget(self.searchable_list.searchbar)
        self.leftLayout.addWidget(self.tipped_list.list)
        self.leftLayout.addWidget(self.tipped_list.view)
        self.leftLayout.addWidget(self.letters)

        self.submitTablePattern = QtWidgets.QPushButton('Submit')
        self.submitTablePattern.clicked.connect(self.submit)

        self.removeAtom = QtWidgets.QPushButton('Remove Atom')
        self.removeAtom.clicked.connect(self.remove_atom)

        self.editLayout.addWidget(self.name)
        self.editLayout.addWidget(self.mainEdit)

        for cb in checkBoxes:
            self.buttonsLayout.addWidget(cb)
        self.buttonsLayout.addWidget(self.removeAtom)
        self.buttonsLayout.addWidget(self.submitTablePattern)

        self.boxesLayout.insertLayout(0, self.leftLayout)
        self.boxesLayout.insertLayout(1, self.editLayout)

        self.mainLayout.insertLayout(0, self.boxesLayout)
        self.mainLayout.insertLayout(1, self.buttonsLayout)

        self.showMaximized()

    def remove_atom(self):
        atom_name = self.tipped_list.list.currentItem().text()
        self.model_launcher.remove_atom(atom_name)
        self.tipped_list.refresh()

    def insert_atom(self):
        atom = self.tipped_list.current_item()
        mode = self.mode.checkedButton().text()
        letter = self.letters.currentText()

        text = str(atom)

        if mode == 'Table':
            text = text.replace(FormulaAtom.LETTER, letter) + ','# немного неправильно

        self.mainEdit.insertPlainText(text)

        self.mainEdit.setFocus()

    def clear_edits(self):
        self.name.clear()
        self.mainEdit.clear()

    def submit(self):
        if not self.name.text():
            return

        try:
            if self.mode.checkedButton().text() == "Table":
                text = self.mainEdit.toPlainText().replace(",\n", "\n").strip(",\n")
                self.model_launcher.write_table(self.name.text(), text)
                self.controller_launcher.refresh_tables()
            else:
                atom_name, named_formula = self.name.text(), self.mainEdit.toPlainText()
                self.model_launcher.write_atom(atom_name, named_formula)
                self.tipped_list.refresh()

            self.clear_edits()
        except ParseException:
            display_error('Syntax error', 'Are you sure, everyting is ok about syntax?')
        except PieceNameError:
            display_error('Name error', 'The name you want to use already exists') #Ещё надо проверить на имя primary атомов
