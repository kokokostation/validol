from shutil import copyfile


def main(model_launcher):
    copyfile('user.db', 'user.db.old')

    for table in model_launcher.get_tables():
        for pattern in model_launcher.get_patterns(table.name):
            model_launcher.write_pattern(pattern)
