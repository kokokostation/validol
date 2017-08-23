from validol.model.store.structures.glued_active.glued_active_view import GluedActiveView
from validol.model.store.miners.weekly_reports.flavors import WEEKLY_REPORT_FLAVORS
from validol.model.store.miners.weekly_reports.flavor_view import WeeklyReportView
from validol.model.store.miners.daily_reports.ice_view import IceView
from validol.model.store.miners.daily_reports.cme_view import CmeView

ALL_VIEW_FLAVORS = [WeeklyReportView(flavor) for flavor in WEEKLY_REPORT_FLAVORS] + \
                   [GluedActiveView(), IceView(), CmeView()]

VIEW_FLAVORS_MAP = {flavor.name(): flavor for flavor in ALL_VIEW_FLAVORS}