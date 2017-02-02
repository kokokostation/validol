from PyQt4 import QtGui, QtCore
import formulae

class TableDialog(QtGui.QWidget):
    def __init__(self, new_table):
        QtGui.QWidget.__init__(self)

        self.new_table = new_table

        self.setWindowTitle("Table edit")

        self.mainLayout = QtGui.QVBoxLayout(self)
        self.boxesLayout = QtGui.QHBoxLayout()
        self.buttonsLayout = QtGui.QHBoxLayout()
        self.editLayout = QtGui.QVBoxLayout()

        self.atomList = QtGui.QListWidget()
        for name, _, presentation in formulae.get_atoms():
            self.add_atom(name, presentation)
        self.atomList.itemDoubleClicked.connect(self.insertAtom)

        self.name = QtGui.QLineEdit()
        self.mainEdit = QtGui.QTextEdit()

        self.submitAtom = QtGui.QPushButton('Submit atom')
        self.submitAtom.clicked.connect(self.submit_atom)

        self.submitTablePattern = QtGui.QPushButton('Submit table pattern')
        self.submitTablePattern.clicked.connect(self.submit_table_pattern)

        self.editLayout.addWidget(self.name)
        self.editLayout.addWidget(self.mainEdit)

        self.buttonsLayout.addWidget(self.submitAtom)
        self.buttonsLayout.addWidget(self.submitTablePattern)

        self.boxesLayout.addWidget(self.atomList)
        self.boxesLayout.insertLayout(1, self.editLayout)

        self.mainLayout.insertLayout(0, self.boxesLayout)
        self.mainLayout.insertLayout(1, self.buttonsLayout)

        self.show()

    def add_atom(self, name, presentation):
        wi = QtGui.QListWidgetItem(name)
        wi.setToolTip(presentation)
        self.atomList.addItem(wi)

    def insertAtom(self):
        self.mainEdit.insertPlainText(self.atomList.currentItem().text())
        self.mainEdit.setFocus()

    def clear_edits(self):
        self.name.clear()
        self.mainEdit.clear()

    def submit_atom(self):
        name, presentation = self.name.text(), self.mainEdit.toPlainText()
        formulae.write_atom(name, presentation, formulae.get_atoms())
        self.add_atom(name, presentation)
        self.clear_edits()

    def submit_table_pattern(self):
        formulae.write_table(self.name.text(), self.mainEdit.toPlainText())
        self.new_table()
        self.clear_edits()