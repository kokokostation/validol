from PyQt5.QtWidgets import QComboBox, QLineEdit
import pandas as pd

from validol.model.store.miners.daily_reports.cme import CmeActives, Active
from validol.model.store.miners.daily_reports.expirations import Expirations
from validol.model.store.miners.daily_reports.daily_view import DailyView, active_df_tolist
from validol.model.store.view.active_info import ActiveInfo
from validol.view.utils.searchable_combo import SearchableComboBox


class CmeView(DailyView):
    def __init__(self, flavor):
        DailyView.__init__(self, Active, CmeActives, flavor)

    def new_active(self, platform, model_launcher):
        active_name = QLineEdit()
        active_name.setPlaceholderText("Active Name")

        archive_file = QComboBox()
        archive_file.addItems(Active.get_archive_files(model_launcher))

        expirations = Expirations(model_launcher).read_df('''
        SELECT DISTINCT
            PlatformCode, ActiveCode, ActiveName
        FROM
            {table}
        ORDER BY
            PlatformCode, ActiveCode
        ''', index_on=False)

        expirations_w = SearchableComboBox()
        expirations_w.setItems(active_df_tolist(expirations))

        info = model_launcher.controller_launcher.show_pdf_helper_dialog(
            self.get_processors(), [active_name, archive_file, expirations_w])

        if info is None:
            return

        CmeActives(model_launcher, self.flavor['name']).write_df(pd.DataFrame([[platform, active_name.text()]],
                                                         columns=['PlatformCode', 'ActiveName']))

        model_launcher.write_pdf_helper(
            ActiveInfo(self, platform, active_name.text()),
            info,
            {
                'expirations': expirations.iloc[expirations_w.currentIndex()].to_dict(),
                'archive_file': archive_file.currentText(),
            })

        model_launcher.controller_launcher.refresh_actives()