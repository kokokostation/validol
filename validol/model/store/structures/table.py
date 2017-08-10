from validol.model.store.structures.pattern import Patterns
from validol.model.store.structures.structure import Structure, Base
from validol.model.utils import flatten
from sqlalchemy import Column, String, PickleType


class Table(Base):
    __tablename__ = 'tables'
    name = Column(String, primary_key=True)
    formula_groups = Column(PickleType)

    def __init__(self, name, formula_groups):
        self.name = name
        self.formula_groups = [table.split(",") for table in formula_groups.split("\n")]

    def all_formulas(self):
        return flatten(self.formula_groups)

    def __str__(self):
        return "{}:\n{}".format(self.name,
                                "\n".join(",".join(line) for line in self.formula_groups))


class Tables(Structure):
    def __init__(self, model_launcher):
        Structure.__init__(self, Table, model_launcher)

    def get_tables(self):
        return self.read()

    def write_table(self, table_name, formula_groups):
        self.write(Table(table_name, formula_groups))

    def remove_table(self, name):
        self.remove_by_name(name)
        Patterns(self.model_launcher).remove_table_patterns(name)

    def get_table(self, name):
        return self.read_by_name(name)