from PyQt5 import QtGui, QtCore
import formulae

class TableDialog(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.mainLayout = QtGui.QHBoxLayout(self)
        self.buttonsLayout = QtGui.QVBoxLayout()
        self.editLayout = QtGui.QVBoxLayout()

        self.atomList = QtGui.QListWidget()

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

        self.mainLayout.addWidget(self.atomList)
        self.mainLayout.insertLayout(1, self.edits)
        self.mainLayout.insertLayout(2, self.editLayout)

        self.showMaximized()

    def clear_edits(self):
        self.name.clear()
        self.mainEdit.clear()

    def submit_item(self):
        formulae.write_atom(self.name.text(), self.mainEdit.text(), formulae.get_atoms())
        self.clear_edits()

    def submit_table_pattern(self):
        formulae.write_table(self.name.text(), [line.split(" ") for line in self.mainEdit.splitlines()])
        self.clear_edits()