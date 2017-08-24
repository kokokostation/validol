from PyQt5 import QtWidgets, QtGui
from pyparsing import alphas

from validol.view.view_element import ViewElement
from validol.model.resource_manager.atom_flavors import FormulaAtom


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

        self.atom_list = QtWidgets.QListWidget()
        self.atom_list.itemDoubleClicked.connect(self.insert_atom)
        self.atoms_map = {}
        self.refresh_atoms()

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

        self.leftLayout.addWidget(self.atom_list)
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

        self.show()

    def remove_atom(self):
        atom_name = self.atom_list.currentItem().text()
        self.model_launcher.remove_atom(atom_name)
        self.refresh_atoms()

    def refresh_atoms(self):
        self.atom_list.clear()
        atoms = self.model_launcher.get_atoms()
        self.atoms_map = {atom.name: atom for atom in atoms}

        for atom in atoms:
            formula = 'primary'
            if isinstance(atom, FormulaAtom):
                formula = atom.formula

            wi = QtWidgets.QListWidgetItem(atom.name)
            wi.setToolTip("{}: {}".format(atom, formula))
            self.atom_list.addItem(wi)

    def insert_atom(self):
        atom = self.atoms_map[self.atom_list.currentItem().text()]
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

        if self.mode.checkedButton().text() == "Table":
            text = self.mainEdit.toPlainText().replace(",\n", "\n").strip(",\n")
            self.model_launcher.write_table(self.name.text(), text)
            self.controller_launcher.refresh_tables()
        else:
            atom_name, named_formula = self.name.text(), self.mainEdit.toPlainText()
            self.model_launcher.write_atom(atom_name, named_formula)
            self.refresh_atoms()

        self.clear_edits()
