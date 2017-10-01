import sqlite3
import re
from validol.model.store.miners.weekly_reports.flavors import Ice
from shutil import copyfile


def main(model_launcher):
    copyfile('main.db', 'main.db.old')

    dbh = sqlite3.connect('main.db')

    res = dbh.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()

    for name in res:
        if any(re.match('^.*{}$'.format(flavor['name']), name[0]) for flavor in Ice.FLAVORS) or \
                re.match('pair_id.*', name[0]):
            dbh.cursor().execute('''
                DROP TABLE IF EXISTS
                    "{table}"
            '''.format(table=name[0]))

    model_launcher.update_weekly()