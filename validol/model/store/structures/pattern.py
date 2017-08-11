from validol.model.store.structures.structure import Structure, Base, JSONCodec
from sqlalchemy import Column, String
from marshmallow import Schema, fields, post_load, pre_dump


class Piece:
    def __init__(self, atom_id, color):
        self.atom_id = atom_id
        self.color = color

    def name(self):
        raise NotImplementedError


class PieceSchema(Schema):
    atom_id = fields.String()
    color = fields.List(fields.Integer())

    @post_load
    def make(self, data):
        return Piece(**data)


class Line(Piece):
    def name(self):
        return "line"


class LineSchema(PieceSchema):
    @post_load
    def make(self, data):
        return Line(**data)


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


class BarSchema(PieceSchema):
    base = fields.Integer()
    sign = fields.Integer()

    @post_load
    def make(self, data):
        return Bar(**data)


class Graph:
    def __init__(self, pieces=None):
        self.pieces = pieces
        if self.pieces is None:
            self.pieces = [[] for _ in range(2)]

    def add_piece(self, lr, piece):
        self.pieces[lr].append(piece)


class SideSchema(Schema):
    lines = fields.Nested(LineSchema, many=True)
    bars = fields.Nested(BarSchema, many=True)

    @post_load
    def make(self, data):
        return data['lines'] + data['bars']

    @pre_dump
    def primitive(self, pieces):
        return {'lines': [piece for piece in pieces if isinstance(piece, Line)],
                'bars': [piece for piece in pieces if isinstance(piece, Bar)]}


class GraphSchema(Schema):
    left = fields.Nested(SideSchema)
    right = fields.Nested(SideSchema)

    @post_load
    def make(self, data):
        return Graph([data['left'], data['right']])

    @pre_dump
    def primitive(self, graph):
        return dict(zip(('left', 'right'), graph.pieces))


class Pattern(Base):
    __tablename__ = "patterns"
    graphs = Column(JSONCodec(GraphSchema(many=True)))
    table_name = Column(String, primary_key=True)
    name = Column(String, primary_key=True)

    def __init__(self, table_name=None, name=None):
        self.graphs = []
        self.table_name = table_name
        self.name = name

    def add_graph(self, graph):
        self.graphs.append(graph)

    def set_name(self, table_name, name):
        self.table_name = table_name
        self.name = name

    def get_formulas(self):
        return [piece.atom_id for graph in self.graphs for lr in graph.pieces for piece in lr]

    @staticmethod
    def name_pred(table_name, name):
        return (Pattern.table_name == table_name) & (Pattern.name == name)


class Patterns(Structure):
    def __init__(self, model_launcher):
        Structure.__init__(self, Pattern, model_launcher)

    def get_patterns(self, table_name):
        return [pattern for pattern in self.read() if pattern.table_name == table_name]

    def write_pattern(self, pattern):
        self.write(pattern)

    def remove_pattern(self, table_name, name):
        self.remove_by_pred(Pattern.name_pred(table_name, name))

    def read_pattern(self, table_name, name):
        self.read(Pattern.name_pred(table_name, name))

    def remove_table_patterns(self, table_name):
        self.remove_by_pred(Pattern.table_name == table_name)
