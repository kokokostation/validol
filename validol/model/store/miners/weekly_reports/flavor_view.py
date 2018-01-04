from validol.model.store.view.view_flavor import ViewFlavor
from validol.model.store.miners.weekly_reports.active import WeeklyActives, Active
from validol.model.store.resource import Platforms


class WeeklyReportView(ViewFlavor):
    def __init__(self, flavor):
        ViewFlavor.__init__(self)
        self.flavor = flavor

    def name(self):
        return self.flavor['name']

    def platforms(self, model_launcher):
        return Platforms(model_launcher, self.flavor['name']).get_platforms()

    def actives(self, platform, model_launcher):
        return WeeklyActives(model_launcher, self.flavor['name']).get_actives(platform)

    def get_df(self, active_info, model_launcher):
        return Active(model_launcher, self.flavor, active_info.platform, active_info.active).read_dates_dt()