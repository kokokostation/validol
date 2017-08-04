import re

from market_graphs.model.store.structures.structure import Structure, Item


class Atom(Item):
    def __init__(self, name, formula, independent):
        Item.__init__(self, name)
        self.formula = formula
        self.independent = independent


class Atoms(Structure):
    def __init__(self):
        Structure.__init__(self, "atoms")

    def get_atoms(self, primary_atoms):
        primary_atoms.extend(self.read())

        return primary_atoms

    @staticmethod
    def if_independent(named_formula, all_atoms):
        pure_atoms = "(?:" + "|".join([re.escape(a.name) for a in all_atoms]) + ")"
        atoms = set(re.findall(pure_atoms, named_formula))
        return not any([a.name in atoms and not a.independent for a in all_atoms])

    def write_atom(self, atom_name, named_formula, all_atoms):
        self.write(Atom(atom_name, named_formula, Atoms.if_independent(named_formula, all_atoms)))

    def remove_atom(self, name):
        self.remove_by_name(name)
