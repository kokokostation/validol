import sqlite3
from shutil import copyfile


def main(model_launcher):
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