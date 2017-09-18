from PyQt5.QtWidgets import QComboBox
import pandas as pd

from validol.model.store.miners.daily_reports.ice import IceActives, Active, IceAllActives
from validol.model.store.miners.daily_reports.daily_view import DailyView, active_df_tolist
from validol.model.store.view.active_info import ActiveInfo
from validol.view.utils.searchable_combo import SearchableComboBox


class IceView(DailyView):
    def __init__(self, flavor):
        DailyView.__init__(self, Active, IceActives, flavor)

    def new_active(self, platform, model_launcher):
        expirations = model_launcher.get_expirations()

        expirations_w = SearchableComboBox()
        expirations_w.setItems(active_df_tolist(expirations))

        actives = IceAllActives(model_launcher, self.flavor['name']).get_actives(platform)

        actives_w = SearchableComboBox()
        actives_w.setItems(active_df_tolist(actives))

        info = model_launcher.controller_launcher.show_pdf_helper_dialog(self.get_processors(), [actives_w, expirations_w])

        if info is None:
            return

        active = actives.iloc[actives_w.currentIndex()]

        IceActives(model_launcher, self.flavor['name']).write_df(pd.DataFrame([active]))

        model_launcher.write_pdf_helper(
            ActiveInfo(self, platform, active.ActiveName),
            info,
            {
                'active_code': active.ActiveCode,
                'expirations': expirations.iloc[expirations_w.currentIndex()].to_dict()
            })

        model_launcher.controller_launcher.refresh_actives()