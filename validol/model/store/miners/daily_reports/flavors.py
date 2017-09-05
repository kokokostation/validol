from validol.model.store.miners.daily_reports.cme import CmeDaily
from validol.model.store.miners.daily_reports.ice import IceDaily
from validol.model.store.resource import Updater
from validol.model.store.miners.daily_reports.ice_flavors import ICE_DAILY_FLAVORS
from validol.model.store.miners.daily_reports.cme_flavors import CME_DAILY_FLAVORS

DAILY_REPORT_FLAVORS = ICE_DAILY_FLAVORS + CME_DAILY_FLAVORS


class DailyReports(Updater):
    def update(self):
        for cls, flavors in ((CmeDaily, CME_DAILY_FLAVORS), (IceDaily, ICE_DAILY_FLAVORS)):
            for flavor in flavors:
                cls(self.model_launcher, flavor).update()
