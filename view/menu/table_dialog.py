from PyQt5 import QtWidgets, QtWidgets
from pyparsing import alphas

from model.store import user_structures, data_parser
from view.view_element import ViewElement


class TableDialog(ViewElement, QtWidgets.QWidget):
    def __init__(self, parent, flags, controller_launcher):
        QtWidgets.QWidget.__init__(self, parent, flags)
        ViewElement.__init__(self, controller_launcher)

        self.setWindowTitle("Table edit")

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.boxesLayout = QtWidgets.QHBoxLayout()
        self.buttonsLayout = QtWidgets.QHBoxLayout()
        self.editLayout = QtWidgets.QVBoxLayout()
        self.leftLayout = QtWidgets.QVBoxLayout()

        self.atomList = QtWidgets.QListWidget()
        for name, _, presentation in user_structures.get_atoms():
            self.add_atom(name, presentation)
        self.atomList.itemDoubleClicked.connect(self.insertAtom)

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

        self.leftLayout.addWidget(self.atomList)
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
        title = self.atomList.currentItem().text()
        if title not in data_parser.primary_labels:
            self.atomList.takeItem(self.atomList.currentRow())
            user_structures.remove_atom(title)

    def add_atom(self, name, presentation):
        wi = QtWidgets.QListWidgetItem(name)
        wi.setToolTip(presentation)
        self.atomList.addItem(wi)

    def insertAtom(self):
        atom = self.atomList.currentItem().text()
        mode = self.mode.checkedButton().text()
        letter = self.letters.currentText()

        if mode == "Table":
            text = atom + "(" + letter + "),"
        else:
            text = atom

        self.mainEdit.insertPlainText(text)

        if mode == "Table" and not letter:
            for _ in "),":
                self.mainEdit.moveCursor(QtGui.QTextCursor.Left)

        self.mainEdit.setFocus()

    def clear_edits(self):
        self.name.clear()
        self.mainEdit.clear()

    def submit(self):
        if not self.name.text():
            return

        if self.mode.checkedButton().text() == "Table":
            text = self.mainEdit.toPlainText().replace(
                ",\n", "\n").strip(",\n")
            user_structures.write_table(self.name.text(), text)
            self.controller_launcher.refresh_tables()
        else:
            name, presentation = self.name.text(), self.mainEdit.toPlainText()
            user_structures.write_atom(
                name, presentation, user_structures.get_atoms())
            self.add_atom(name, presentation)

        self.clear_edits()
