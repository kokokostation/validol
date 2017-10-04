import os
from zipfile import ZipFile
from shutil import copyfile

from validol.model.store.miners.daily_reports.cme import Active
from validol.model.store.miners.daily_reports.pdf_helpers.cme import CmeParser
from validol.model.store.miners.daily_reports.cme_view import CmeView
from validol.model.store.miners.daily_reports.cme_flavors import CME_DAILY_FLAVORS


def main(model_launcher):
    copyfile('main.db', 'main.db.old')

    bulletin_dir = 'Bulletin'

    bad_files = set()

    for file in os.listdir(bulletin_dir):
        path = os.path.join(bulletin_dir, file)
        if Active.Cache.if_valid_zip(file) and CmeParser.if_preliminary_zip(ZipFile(path)):
            os.rename(path, os.path.join(bulletin_dir, 'PRELIMINARY_{}'.format(file)))
            bad_files.add(file)

    for flavor in CME_DAILY_FLAVORS:
        view_flavor = CmeView(flavor)

        for ai in view_flavor.all_actives(model_launcher, False):
            view_flavor.remove_active_data(ai, model_launcher)

    model_launcher.update_daily()

    leak_files = bad_files - set(os.listdir(bulletin_dir))

    if leak_files:
        with open('leaked_files.txt', 'w') as file:
            file.write('\n'.join(leak_files))