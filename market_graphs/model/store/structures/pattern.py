from market_graphs.model.store.structures.structure import Structure, Item


class Piece:
    def __init__(self, atom_id, color):
        self.atom_id = atom_id
        self.color = color

    def name(self):
        raise NotImplementedError


class Line(Piece):
    def name(self):
        return "line"


class Bar(Piece):
    def __init__(self, atom_id, color, base, sign):
        Piece.__init__(self, atom_id, color)
        self.base = base
        self.sign = sign

    def name(self):
        if self.sign == 1:
            return "bar"
        else:
            return "-bar"


class Graph:
    def __init__(self):
        self.pieces = [[] for _ in range(2)]

    def add_piece(self, lr, piece):
        self.pieces[lr].append(piece)


class Pattern(Item):
    def __init__(self, table_name=None, pattern_name=None):
        Item.__init__(self, pattern_name)
        self.graphs = []
        self.table_name = table_name

    def add_graph(self, graph):
        self.graphs.append(graph)

    def set_name(self, table_name, pattern_name):
        self.table_name = table_name
        self.name = pattern_name

    def get_formulas(self):
        return [piece.atom_id for graph in self.graphs for lr in graph.pieces for piece in lr]


class Patterns(Structure):
    def __init__(self):
        Structure.__init__(self, "patterns")

    def get_patterns(self, table_name):
        return [pattern for pattern in self.read() if pattern.table_name == table_name]

    def write_pattern(self, pattern):
        self.write(pattern)

    def remove_pattern(self, table_name, pattern_name):
        self.remove_by_pred(
            lambda pattern: pattern.table_name == table_name and
                            pattern.name == pattern_name)

    def remove_table_patterns(self, table_name):
        self.remove_by_pred(lambda pattern: pattern.table_name == table_name)
