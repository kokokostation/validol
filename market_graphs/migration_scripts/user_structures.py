import os

from market_graphs.model.launcher import ModelLauncher
from market_graphs.model.store.structures.pattern import Pattern, Line, Bar, Graph
from market_graphs.model.store.structures.structure import Structure
from market_graphs.view.menu.graph_dialog import GraphDialog


def map_atoms(atoms, model_launcher):
    for name, _, named_formula in atoms:
        model_launcher.write_atom(name, named_formula)


def map_tables(tables, model_launcher):
    for name, formula_groups, _ in tables:
        model_launcher.write_table(name, formula_groups)


def map_pieces(pieces, table_labels):
    lines, bars, mbars = pieces
    result = []

    for atom_id, color in lines:
        result.append(Line(table_labels[atom_id], GraphDialog.COLORS[color]))

    for ((atom_id, base, color), sign) in [(bar, 1) for bar in bars] + \
            [(mbar, -1) for mbar in mbars]:
        result.append(Bar(table_labels[atom_id], GraphDialog.COLORS[color], base, sign))

    return result


def map_patterns(patterns, model_launcher):
    for table_name, pattern_name, pattern in patterns:
        new_pattern = Pattern(table_name, pattern_name)

        for graph in pattern:
            new_graph = Graph()

            for i, section in enumerate(graph):
                new_graph.pieces[i] = map_pieces(
                    section, model_launcher.get_table(table_name).all_formulas())

            new_pattern.add_graph(new_graph)

        model_launcher.write_pattern(new_pattern)


def main():
    model_launcher = ModelLauncher(False)

    for name, mapper in (
        ("atoms", map_atoms),
        ("tables", map_tables),
        ("patterns", map_patterns)
    ):
        content = Structure(name).read()
        os.rename(name, "{}.old".format(name))
        open(name, "w").close()
        mapper(content, model_launcher)

if __name__ == '__main__':
    main()
