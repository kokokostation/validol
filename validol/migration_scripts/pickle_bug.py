from validol.model.store.structures.pattern import Pattern, Graph, Line, Bar
from validol.model.launcher import ModelLauncher
from validol.model.store.miners.prices import InvestingPrices

from market_graphs.model.store.structures.atom import Atoms
import market_graphs.model.store.structures.pattern as pattern
from market_graphs.model.store.structures.table import Tables
from market_graphs.model.store.miners.prices import InvestingPrices as investingPrices
from market_graphs.model.launcher import ModelLauncher as modelLauncher

import pickle
from io import BytesIO


class RenamingUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        return super().find_class(module.replace('validol', 'market_graphs'), name)


def loads(bytes):
    file = BytesIO(bytes)
    unpickler = RenamingUnpickler(file)
    return unpickler.load()


pickle.loads = loads


def main():
    model_launcher = modelLauncher().init_user()
    new_model_launcher = ModelLauncher().init_user('user.db.new')

    for item in Atoms(model_launcher).read():
        new_model_launcher.write_atom(item.name, item.formula)

    for item in pattern.Patterns(model_launcher).read():
        new_pattern = Pattern(item.table_name, item.name)

        def map_piece(piece):
            if isinstance(piece, pattern.Line):
                return Line(piece.atom_id, piece.color)
            else:
                return Bar(piece.atom_id, piece.color, piece.base, piece.sign)

        def map_graph(graph):
            return Graph([[map_piece(piece) for piece in lr] for lr in graph.pieces])

        new_pattern.graphs = [map_graph(graph) for graph in item.graphs]

        new_model_launcher.write_pattern(new_pattern)

    for item in Tables(model_launcher).read():
        new_model_launcher.write_table(item.name, str(item))

    ip = InvestingPrices(new_model_launcher)
    for item in investingPrices(model_launcher).read():
        ip.get_info_through_url(item.url)


if __name__ == '__main__':
    main()