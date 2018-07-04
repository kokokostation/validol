from validol.model.store.resource import FlavorUpdater
from validol.model.store.collectors.ml import MlCurves, MlCurve
from validol.model.store.miners.daily_reports.flavors import DAILY_REPORT_FLAVORS
from validol.model.store.miners.daily_reports.moex import MOEX


class DailyReports(FlavorUpdater):
    def __init__(self, model_launcher):
        FlavorUpdater.__init__(self, model_launcher, DAILY_REPORT_FLAVORS + [MOEX])

    def update_flavor(self, flavor):
        return flavor['updater'](self.model_launcher, flavor).update()

    def flavor_dependencies(self, flavor):
        if flavor.get('options', False):
            return [(MlCurves, [MlCurve.flavor(flavor['name'])])]
        else:
            return []