from validol.model.store.view.view_flavor import ViewFlavor
from validol.model.store.miners.daily_reports.ice import IceActives, Active
from validol.model.store.miners.weekly_reports.flavor import Platforms


class IceView(ViewFlavor):
    def name(self):
        return Active.FLAVOR

    def platforms(self, model_launcher):
        return Platforms(model_launcher, Active.FLAVOR).get_platforms()

    def actives(self, platform, model_launcher):
        return IceActives(model_launcher).get_actives(platform)

    def active_flavors(self, platform, active, model_launcher):
        return Active(model_launcher, platform, active).get_flavors()

    def get_df(self, platform, active, active_flavor, model_launcher):
        return Active(model_launcher, platform, active).get_flavor(active_flavor)

    def switch_update(self, platform, active, model_launcher):
        Active(model_launcher, platform, active).switch_update()