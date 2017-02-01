import os
import filenames
from evaluator import NumericStringParser
import utils
import re
from pyparsing import alphas

def compile_formula(formula):
    return NumericStringParser().eval(formula)

def parse_atom(atom):
    name, index = atom[:-1].split("(")
    return name, alphas.index(index)

def get_tables():
    result = []
    if not os.path.isfile(filenames.tablesFile):
        return result

    file = open(filenames.tablesFile, "r")
    for table in file.read().splitlines():
        name, activesNum, atom_groups = table.split("\t", 1)
        result.append((name, (int(activesNum), [[parse_atom(atom) for atom in group.split("~")] for group in atom_groups.split("\t")])))
    file.close()

    return result

def write_table(name, atom_groups):
    activesNum = alphas.index(max(re.findall(r'\(([A-Z])\)', "".join(utils.flatten(atom_groups))))) + 1

    file = open(filenames.tablesFile, "a+")
    file.write(name + "\t" + str(activesNum) + "\t" + "\t".join(["~".join(atoms) for atoms in atom_groups]))
    file.close()

def get_atoms():
    result = []
    if not os.path.isfile(filenames.atomsFile):
        return result

    file = open(filenames.atomsFile, "r")
    result = [line.split("\t") for line in file.read().splitlines()]
    file.close()

    return result

def write_atom(name, formula, atoms):
    presentation = formula
    for i in range(len(atoms)):
        formula.replace(atoms[i][0], '~' + str(i))

    file = open(filenames.atomsFile, "a+")
    file.write(name + "\t" + formula + "\t" + presentation + "\n")
    file.close()
