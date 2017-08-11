from validol.model.store.structures.glued_active.glued_active_view import GluedActiveView
from validol.model.store.miners.weekly_reports.flavors import WEEKLY_REPORT_FLAVORS
from validol.model.store.miners.weekly_reports.flavor_view import WeeklyReportView

ALL_VIEW_FLAVORS = [WeeklyReportView(flavor) for flavor in WEEKLY_REPORT_FLAVORS] + \
                   [GluedActiveView()]

VIEW_FLAVORS_MAP = {flavor.name(): flavor for flavor in ALL_VIEW_FLAVORS}