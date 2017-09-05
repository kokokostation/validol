from PyQt5.QtWidgets import QComboBox
import pandas as pd

from validol.model.store.miners.daily_reports.ice import IceActives, Active, IceAllActives
from validol.model.store.miners.daily_reports.expirations import Expirations
from validol.model.store.miners.daily_reports.daily_view import DailyView, active_df_tolist
from validol.model.store.view.active_info import ActiveInfo


class IceView(DailyView):
    def __init__(self, flavor):
        DailyView.__init__(self, Active, IceActives, flavor)

    def new_active(self, platform, model_launcher, controller_launcher):
        actives = IceAllActives(model_launcher, self.flavor['name']).get_actives(platform)

        expirations_w = QComboBox()

        curr_expirations = pd.DataFrame()

        def change_expirations(a0):
            nonlocal curr_expirations

            curr_expirations = Expirations(model_launcher).read_df(
                '''
                SELECT DISTINCT
                    PlatformCode, ActiveCode, ActiveName
                FROM
                    {table}
                WHERE
                    PlatformCode = ? AND ActiveCode = ?''',
                params=(actives.loc[a0, 'PlatformCode'], actives.loc[a0, 'ActiveCode']),
                index_on=False)

            expirations_w.clear()
            expirations_w.addItems(active_df_tolist(curr_expirations))

        actives_w = QComboBox()
        actives_w.addItems(active_df_tolist(actives))
        actives_w.currentIndexChanged.connect(change_expirations)
        actives_w.activated.connect(change_expirations)

        info = controller_launcher.show_pdf_helper_dialog(self.get_processors(), [actives_w, expirations_w])

        if info is None:
            return

        active = actives.iloc[actives_w.currentIndex()]

        IceActives(model_launcher, self.flavor['name']).write_df(pd.DataFrame([active]))

        model_launcher.write_pdf_helper(
            ActiveInfo(self, platform, active.ActiveName),
            info,
            {
                'active_code': active.ActiveCode,
                'expirations': curr_expirations.iloc[expirations_w.currentIndex()].to_dict()
            })

        controller_launcher.refresh_actives()