from shutil import copyfile


def main(model_launcher):
    copyfile('main.db', 'main.db.old')

    model_launcher.main_dbh.cursor().execute('ALTER TABLE Monetary RENAME TO Monetary_MBase;')
    model_launcher.main_dbh.commit()
