import os
import filenames
from evaluator import NumericStringParser
import utils
import re
from pyparsing import alphas
import data_parser

def compile_formula(formula):
    return NumericStringParser().eval(formula)

def parse_atom(atom):
    name, index = atom[:-1].split("(")
    return name, alphas.index(index)

def parse_formula(formula):
    atoms = list(set(re.findall(r'[A-z]+\([A-Z]\)', formula)))
    parsed_atoms = list(map(parse_atom, atoms))
    for i in range(len(atoms)):
        formula = formula.replace(atoms[i], "~" + str(i))

    return parsed_atoms, formula

def get_tables():
    result = []
    if not os.path.isfile(filenames.tablesFile):
        return result

    file = open(filenames.tablesFile, "r")
    for table in file.read().splitlines():
        name, atom_groups = table.split("\t", 1)
        result.append((name, atom_groups.replace("\t", "\n"), [[parse_formula(formula) for formula in group.split(",")] for group in atom_groups.split("\t")]))
    file.close()

    return result

def write_table(name, atom_groups):
    file = open(filenames.tablesFile, "a+")
    file.write(name + "\t" + atom_groups.replace("\n", "\t") + "\n")
    file.close()

def get_atoms():
    result = [(data_parser.primary_labels[i], "~" + str(i), data_parser.primary_labels[i]) for i in range(len(data_parser.primary_labels))]

    if not os.path.isfile(filenames.atomsFile):
        return result

    file = open(filenames.atomsFile, "r")
    result.extend([line.split("\t") for line in file.read().splitlines()])
    file.close()

    return result

def write_atom(atomName, presentation, atoms):
    atomFormula = presentation
    for name, formula, _ in atoms:
        atomFormula = atomFormula.replace(name, "(" + formula + ")")

    file = open(filenames.atomsFile, "a+")
    file.write(atomName + "\t" + atomFormula + "\t" + presentation + "\n")
    file.close()
