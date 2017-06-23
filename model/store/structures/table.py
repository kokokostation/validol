import re

from pyparsing import alphas

from model.store.structures.pattern import Patterns
from model.store.structures.structure import Structure, Item


class Table(Item):
    def __init__(self, name, atom_groups, formulae):
        Item.__init__(self, name)
        self.atom_groups = atom_groups
        self.formulae = formulae

    @staticmethod
    def parse_atom(atom):
        name, index = atom[:-1].split("(")
        return name, alphas.index(index)

    @staticmethod
    def parse_formula(formula, all_atoms):
        pure_atoms = "(?:" + "|".join([re.escape(a.name) for a in all_atoms]) + ")"
        atoms = list(set(re.findall(pure_atoms + '\([A-Z]\)', formula)))
        parsed_atoms = list(map(Table.parse_atom, atoms))
        for i, atom in enumerate(atoms):
            formula = formula.replace(atom, "~" + str(i))

        return parsed_atoms, formula

    @staticmethod
    def factory(table_name, atom_groups, all_atoms):
        atom_groups = [table.split(",") for table in atom_groups.split("\n")]
        formulae = [list(map(lambda formula: Table.parse_formula(formula, all_atoms), formula)) for formula in atom_groups]
        return Table(table_name, atom_groups, formulae)


class Tables(Structure):
    def __init__(self):
        Structure.__init__(self, "tables")

    def get_tables(self):
        return self.read()

    def write_table(self, table_name, atom_groups, all_atoms):
        self.write(Table.factory(table_name, atom_groups, all_atoms))

    def remove_table(self, name):
        self.remove_by_name(name)
        Patterns().remove_table_patterns(name)