from shutil import copyfile

from validol.model.store.miners.daily_reports.expirations import Expirations
from validol.model.store.miners.daily_reports.ice_view import IceView
from validol.model.store.miners.daily_reports.ice_flavors import ICE_DAILY_FLAVORS
from validol.model.store.miners.daily_reports.cme_view import CmeView
from validol.model.store.miners.daily_reports.cme_flavors import CME_DAILY_FLAVORS


def main(model_launcher):
    copyfile('main.db', 'main.db.old')

    model_launcher.main_dbh.cursor().execute('DROP TABLE IF EXISTS "Expirations"')

    Expirations(model_launcher).update()

    for view, flavors in ((CmeView, CME_DAILY_FLAVORS), (IceView, ICE_DAILY_FLAVORS)):
        for flavor in flavors:
            view_flavor = view(flavor)

            for ai in view_flavor.all_actives(model_launcher, False):
                ai.flavor.reload_expirations(ai, model_launcher)