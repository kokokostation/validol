import re

from validol.model.store.structures.structure import Structure
from validol.model.resource_manager.atom_flavors import FormulaAtom


class Atoms(Structure):
    def __init__(self, model_launcher):
        Structure.__init__(self, FormulaAtom, model_launcher)

    def get_atoms(self, primary_atoms):
        primary_atoms.extend(self.read())

        return primary_atoms

    def write_atom(self, atom_name, named_formula):
        match = re.match("(.*)\((.*)\)", atom_name)
        name, params = match.group(1), re.split(",\s*", match.group(2))
        if re.search('\S', match.group(2)) is None:
            params = []

        self.write(FormulaAtom(name, named_formula, params))

    def remove_atom(self, name):
        self.remove_by_name(name)
