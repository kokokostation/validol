import os
import filenames
import re
from pyparsing import alphas
import data_parser
import pickle
import utils


def parse_atom(atom):
    name, index = atom[:-1].split("(")
    return name, alphas.index(index)


def parse_formula(formula):
    pure_atoms = "(?:" + "|".join([re.escape(a[0]) for a in get_atoms()]) + ")"
    atoms = list(set(re.findall(pure_atoms + '\([A-Z]\)', formula)))
    parsed_atoms = list(map(parse_atom, atoms))
    for i in range(len(atoms)):
        formula = formula.replace(atoms[i], "~" + str(i))

    return parsed_atoms, formula


def get_tables():
    result = []
    if not os.path.isfile(filenames.tablesFile):
        return result

    with open(filenames.tablesFile, "rb") as file:
        result = utils.pickleLoader(file)

    return result


def write_table(name, atom_groups):
    with open(filenames.tablesFile, "ab") as file:
        pickle.dump((name, atom_groups, [list(map(parse_formula, formulas.split(
            ","))) for formulas in atom_groups.split("\n")]), file)


def remove_table(name):
    remove_by_name(lambda a: a[0] == name, filenames.tablesFile, get_tables())
    remove_by_name(
        lambda a: a[0] == name, filenames.patternsFile, get_patterns())


def get_atoms():
    result = [(data_parser.primary_labels[i], "~" + str(i), data_parser.primary_labels[i])
              for i in range(len(data_parser.primary_labels))]

    if not os.path.isfile(filenames.atomsFile):
        return result

    with open(filenames.atomsFile, "rb") as file:
        result.extend(utils.pickleLoader(file))

    return result


def write_atom(atomName, presentation, atoms):
    atomFormula = presentation
    for name, formula, _ in sorted(atoms, key=lambda x: -len(x[0])):
        atomFormula = atomFormula.replace(name, "(" + formula + ")")

    with open(filenames.atomsFile, "ab") as file:
        pickle.dump((atomName, atomFormula, presentation), file)


def remove_atom(name):
    remove_by_name(lambda a: a[0] == name, filenames.atomsFile, get_atoms()[
                   len(data_parser.primary_labels):])


def remove_by_name(pred, fileName, l):
    with open(fileName, "wb") as file:
        for a in l:
            if not pred(a):
                pickle.dump(a, file)


def get_patterns():
    result = {}

    if not os.path.isfile(filenames.patternsFile):
        return result

    with open(filenames.patternsFile, "rb") as file:
        result = utils.pickleLoader(file)

    return result


def add_pattern(table, title, pattern):
    with open(filenames.patternsFile, "ab") as file:
        pickle.dump((table, title, pattern), file)


def remove_pattern(table, title):
    remove_by_name(
        lambda a: a[:2] == (table, title), filenames.patternsFile, get_patterns())
