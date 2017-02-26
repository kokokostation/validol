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

    file = open(filenames.tablesFile, "rb")
    result = utils.pickleLoader(file)
    file.close()

    return result

def write_table(name, atom_groups):
    file = open(filenames.tablesFile, "ab")
    pickle.dump((name, atom_groups, [list(map(parse_formula, formulas.split(","))) for formulas in atom_groups.split("\n")]), file)
    file.close()

def remove_table(name):
    remove_by_name(lambda a: a[0] == name, filenames.tablesFile, get_tables())
    remove_by_name(lambda a: a[0] == name, filenames.patternsFile, get_patterns())

def get_atoms():
    result = [(data_parser.primary_labels[i], "~" + str(i), data_parser.primary_labels[i]) for i in range(len(data_parser.primary_labels))]

    if not os.path.isfile(filenames.atomsFile):
        return result

    file = open(filenames.atomsFile, "rb")
    result.extend(utils.pickleLoader(file))
    file.close()

    return result

def write_atom(atomName, presentation, atoms):
    atomFormula = presentation
    for name, formula, _ in sorted(atoms, key=lambda x: -len(x[0])):
        atomFormula = atomFormula.replace(name, "(" + formula + ")")

    file = open(filenames.atomsFile, "ab")
    pickle.dump((atomName, atomFormula, presentation), file)
    file.close()

def remove_atom(name):
    remove_by_name(lambda a: a[0] == name, filenames.atomsFile, get_atoms()[len(data_parser.primary_labels):])

def remove_by_name(pred, fileName, l):
    file = open(fileName, "wb")
    for a in l:
        if not pred(a):
            pickle.dump(a, file)
    file.close()

def get_patterns():
    result = {}

    if not os.path.isfile(filenames.patternsFile):
        return result

    file = open(filenames.patternsFile, "rb")
    result = utils.pickleLoader(file)
    file.close()

    return result

def add_pattern(table, title, pattern):
    file = open(filenames.patternsFile, "ab")
    pickle.dump((table, title, pattern), file)
    file.close()

def remove_pattern(table, title):
    remove_by_name(lambda a: a[:2] == (table, title), filenames.patternsFile, get_patterns())