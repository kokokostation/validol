import sqlite3
import pandas as pd
from shutil import copyfile

from validol.model.resource_manager.resource_manager import ResourceManager


def main():
    copyfile('user.db', 'user.db.old')

    dbh = sqlite3.connect('user.db')

    atoms = pd.read_sql('select * from atoms', dbh)

    plus = {atom['name']: '()' if atom['independent'] else '(@letter)'
            for index, atom in atoms.iterrows()}

    plus.update({
        atom.name: '()' if not atom.params else '(@letter)'
        for atom in ResourceManager.get_primary_atoms()
    })

    def f(row):
        skeys = list(sorted(plus.keys(), key=lambda x: -len(x)))

        for i, key in enumerate(skeys):
            row['formula'] = row['formula'].replace(key, '`' * (len(skeys) - i))

        for i, key in enumerate(skeys):
            row['formula'] = row['formula'].replace('`' * (len(skeys) - i), key + plus[key])

        row['params'] = '[]' if row['independent'] else '["@letter"]'

        return row

    atoms = atoms.apply(f, axis=1)

    del atoms['independent']

    dbh.cursor().execute('drop table atoms')
    dbh.commit()
    dbh.cursor().execute('create table atoms (name text primary key, formula text, params text)')

    atoms.to_sql('atoms', dbh, if_exists='append', index=False)


if __name__ == '__main__':
    main()