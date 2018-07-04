from validol.model.store.miners.weekly_reports.flavor_view import WeeklyReportView
from validol.model.store.miners.weekly_reports.active import Active


def active_iterator(flavor, model_launcher):
    view_flavor = WeeklyReportView(flavor)

    for i, platform in view_flavor.platforms(model_launcher).iterrows():
        for j, active in view_flavor.actives(platform.PlatformCode, model_launcher).iterrows():
            yield Active(model_launcher, flavor, platform.PlatformCode, active.ActiveName)