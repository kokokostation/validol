from validol.model.store.structures.structure import NamedStructure
from validol.model.resource_manager.atom_flavors import FormulaAtom
from validol.model.resource_manager.evaluator import AtomGrammar


class Atoms(NamedStructure):
    def __init__(self, model_launcher):
        NamedStructure.__init__(self, FormulaAtom, model_launcher)

    def get_atoms(self, primary_atoms):
        primary_atoms.extend(self.read())

        return primary_atoms

    def write_atom(self, atom_name, named_formula):
        parsed = AtomGrammar(self.model_launcher.get_atoms()).parse(atom_name, named_formula)

        self.write(FormulaAtom(parsed['name'], named_formula, parsed['vars']))

    def remove_atom(self, name):
        self.remove_by_name(name)
