from market_graphs.model.store.structures.pattern import Patterns
from market_graphs.model.store.structures.structure import Structure, Item
from market_graphs.model.utils import flatten


class Table(Item):
    def __init__(self, name, formula_groups):
        Item.__init__(self, name)
        self.formula_groups = [table.split(",") for table in formula_groups.split("\n")]

    def all_formulas(self):
        return flatten(self.formula_groups)

    def __str__(self):
        return "{}:\n{}".format(self.name,
                                "\n".join(",".join(line) for line in self.formula_groups))


class Tables(Structure):
    def __init__(self):
        Structure.__init__(self, "tables")

    def get_tables(self):
        return self.read()

    def write_table(self, table_name, formula_groups):
        self.write(Table(table_name, formula_groups))

    def remove_table(self, name):
        self.remove_by_name(name)
        Patterns().remove_table_patterns(name)