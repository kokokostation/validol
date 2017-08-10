import re

from validol.model.store.structures.structure import Structure, Base
from sqlalchemy import Column, String, Boolean


class Atom(Base):
    __tablename__ = "atoms"
    name = Column(String, primary_key=True)
    formula = Column(String)
    independent = Column(Boolean)

    def __init__(self, name, formula, independent):
        self.name = name
        self.formula = formula
        self.independent = independent


class Atoms(Structure):
    def __init__(self, model_launcher):
        Structure.__init__(self, Atom, model_launcher)

    def get_atoms(self, primary_atoms):
        primary_atoms.extend(self.read())

        return primary_atoms

    @staticmethod
    def depends_on(named_formula, all_atoms):
        pure_atoms = "(?:{})".format("|".join([re.escape(a.name) for a in all_atoms]))
        return set(re.findall(pure_atoms, named_formula))

    @staticmethod
    def if_independent(named_formula, all_atoms):
        return not any([a.name in Atoms.depends_on(named_formula, all_atoms) and not a.independent
                        for a in all_atoms])

    def write_atom(self, atom_name, named_formula, all_atoms):
        self.write(Atom(atom_name, named_formula, Atoms.if_independent(named_formula, all_atoms)))

    def remove_atom(self, name):
        self.remove_by_name(name)
