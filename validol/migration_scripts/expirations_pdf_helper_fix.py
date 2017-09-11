import sqlite3
import pandas as pd
from shutil import copyfile

from validol.model.resource_manager.resource_manager import ResourceManager


def main():
    copyfile('main.db', 'main.db.old')

    dbh = sqlite3.connect('main.db')

    dbh.cursor().execute('''
        ALTER TABLE 
            Expirations
        ADD COLUMN
            Source TEXT DEFAULT 'net'
    ''')


if __name__ == '__main__':
    main()