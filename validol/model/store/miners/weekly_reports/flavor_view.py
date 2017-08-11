from validol.model.store.view.view_flavor import ViewFlavor
from validol.model.store.miners.weekly_reports.flavor import Platforms, Actives, Active


class WeeklyReportView(ViewFlavor):
    def __init__(self, flavor):
        ViewFlavor.__init__(self)
        self.flavor = flavor

    def name(self):
        return self.flavor['name'].upper()

    def platforms(self, model_launcher):
        return Platforms(model_launcher, self.flavor).get_platforms()

    def actives(self, platform, model_launcher):
        return Actives(model_launcher, self.flavor).get_actives(platform)

    def get_df(self, platform, active, model_launcher):
        return Active(model_launcher, self.flavor, platform, active).read_dates()