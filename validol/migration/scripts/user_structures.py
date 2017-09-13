import pickle
import re

from validol.model.launcher import ModelLauncher
from validol.model.store.structures.pattern import Pattern, Line, Bar, Graph
from validol.model.store.structures.atom import Atoms, Atom
from validol.view.menu.graph_dialog import GraphDialog
from validol.model.store.miners.prices import InvestingPrices


def map_atoms(atoms, model_launcher):
    formulae = {name: named_formula for name, _, named_formula in atoms}

    for atom_name in formulae.keys():
        write_atom(atom_name, formulae, model_launcher)


def write_atom(atom_name, formulae, model_launcher):
    if atom_name not in [atom.name for atom in model_launcher.get_atoms()]:
        depends = Atoms.depends_on(formulae[atom_name],
                                   [Atom(name, name, True) for name in formulae.keys()])
        for name in depends:
            write_atom(name, formulae, model_launcher)

        model_launcher.write_atom(atom_name, formulae[atom_name])


def subf(matchobj):
    return matchobj.group(1)


def map_formula_groups(formula_groups, independent_names):
    pattern = "({})\([A-Z]\)".format("|".join(independent_names))
    return re.sub(pattern, subf, formula_groups)


def map_tables(tables, model_launcher):
    independent_names = [atom.name for atom in model_launcher.get_atoms() if atom.independent]

    for name, formula_groups, _ in tables:
        model_launcher.write_table(name, map_formula_groups(formula_groups, independent_names))


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


def map_prices(model_launcher):
    prices = InvestingPrices(model_launcher)

    with open("prices/pair_ids", "r") as file:
        for line in file:
            url = line.split()[0]
            prices.get_info_through_url(url)


def read(file_name):
    with open(file_name, "rb") as file:
        result = []
        try:
            while True:
                result.append(pickle.load(file))
        except EOFError:
            return result

def main():
    model_launcher = ModelLauncher().init_user()

    for name, mapper in (
        ("atoms", map_atoms),
        ("tables", map_tables),
        ("patterns", map_patterns)
    ):
        content = read(name)
        mapper(content, model_launcher)

    map_prices(model_launcher)

if __name__ == '__main__':
    main()
