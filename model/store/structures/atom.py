from model.store.structures.structure import Structure, Item
from model.store.structures.table import Tables


class Atom(Item):
    def __init__(self, name, formula_to_compile, named_formula):
        Item.__init__(self, name)
        self.formula_to_compile = formula_to_compile
        self.named_formula = named_formula

    @staticmethod
    def factory(atom_name, named_formula, existing_atoms):
        formula_to_compile = named_formula
        for atom in sorted(existing_atoms, key=lambda x: -len(x.name)):
            formula_to_compile = formula_to_compile.replace(atom.name,
                                                            "(" + atom.formula_to_compile + ")")

        return Atom(atom_name, formula_to_compile, named_formula)


class Atoms(Structure):
    def __init__(self):
        Structure.__init__(self, "atoms")

    def get_atoms(self, primary_atoms):
        result = [Atom(atom_name, "~" + str(i), atom_name)
                  for i, atom_name in enumerate(primary_atoms)]

        result.extend(self.read())

        return result

    def write_atom(self, atom_name, named_formula, existing_atoms):
        self.write(Atom.factory(atom_name, named_formula, existing_atoms))

    def remove_atom(self, name):
        self.remove_by_name(name)

        tables = Tables()
        for table in tables.get_tables():
            if name in table:
                tables.remove_table(table.name)
