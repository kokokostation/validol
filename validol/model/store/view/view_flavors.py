from validol.model.store.structures.multiple_active.glued_active import GluedActiveView
from validol.model.store.miners.weekly_reports.flavors import WEEKLY_REPORT_FLAVORS
from validol.model.store.miners.weekly_reports.flavor_view import WeeklyReportView
from validol.model.store.miners.daily_reports.ice_view import IceView
from validol.model.store.miners.daily_reports.ice_flavors import ICE_DAILY_FLAVORS
from validol.model.store.miners.daily_reports.cme_view import CmeView
from validol.model.store.miners.daily_reports.cme_flavors import CME_DAILY_FLAVORS
from validol.model.store.structures.multiple_active.active_set import ActiveSetView


ALL_VIEW_FLAVORS = sum([[view(flavor) for flavor in flavors]
                       for view, flavors in ((WeeklyReportView, WEEKLY_REPORT_FLAVORS),
                                             (IceView, ICE_DAILY_FLAVORS),
                                             (CmeView, CME_DAILY_FLAVORS))],
                       [GluedActiveView(), ActiveSetView()])

VIEW_FLAVORS_MAP = {flavor.name(): flavor for flavor in ALL_VIEW_FLAVORS}