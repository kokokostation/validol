from os import remove, chdir

from model import utils
from model.store import filenames
from model.store.user_structures import write_table

if __name__ == "__main__":
    chdir("../data")

    with open(filenames.tablesFile, "rb") as file:
        result = utils.pickle_loader(file)

    remove(filenames.tablesFile)

    for name, atom_groups, _ in result:
        write_table(name, atom_groups)