class ViewFlavor:
    def __init__(self, model_launcher):
        self.model_launcher = model_launcher

    def platforms(self):
        raise NotImplementedError

    def actives(self, platform):
        raise NotImplementedError

    def name(self):
        raise NotImplementedError

    def get_df(self, platform, active):
        raise NotImplementedError


def all_view_flavors(model_launcher):
    from validol.model.store.structures.glued_active import GluedActiveView
    from validol.model.store.miners.weekly_reports.flavors import WEEKLY_REPORT_FLAVORS
    from validol.model.store.miners.weekly_reports.flavor import WeeklyReportView

    return [WeeklyReportView(flavor, model_launcher) for flavor in WEEKLY_REPORT_FLAVORS] + \
           [GluedActiveView(model_launcher)]