from validol.model.store.structures.pattern import Patterns
from validol.model.store.structures.structure import NamedStructure, Base, JSONCodec
from validol.model.utils.utils import flatten
from validol.model.resource_manager.evaluator import FormulaGrammar

from sqlalchemy import Column, String
import pyparsing as pp


class TableParser(FormulaGrammar):
    def split(self, expr):
        bnf = pp.delimitedList(pp.Combine(self.bnf))

        return list(bnf.parseString(expr, True))


class Table(Base):
    __tablename__ = 'tables'
    name = Column(String, primary_key=True)
    formula_groups = Column(JSONCodec())

    def __init__(self, name, formula_groups, all_atoms):
        self.name = name
        parser = TableParser([atom.name for atom in all_atoms])
        self.formula_groups = [parser.split(table.strip(', ')) for table in formula_groups.split("\n")]

    def all_formulas(self):
        return flatten(self.formula_groups)

    def __str__(self):
        return "{}:\n{}".format(self.name,
                                "\n".join(",".join(line) for line in self.formula_groups))


class Tables(NamedStructure):
    def __init__(self, model_launcher):
        NamedStructure.__init__(self, Table, model_launcher)

    def get_tables(self):
        return self.read()

    def write_table(self, table_name, formula_groups, all_atoms):
        self.write(Table(table_name, formula_groups, all_atoms))

    def remove_table(self, name):
        self.remove_by_name(name)
        Patterns(self.model_launcher).remove_table_patterns(name)

    def get_table(self, name):
        return self.read_by_name(name)