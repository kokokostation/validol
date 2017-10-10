from PyQt5.QtWidgets import QLineEdit
import pandas as pd

from validol.model.store.miners.daily_reports.cme import CmeActives, Active
from validol.model.store.miners.daily_reports.daily_view import DailyView, expirations_layout, \
    searchable_with_mark
from validol.model.store.view.active_info import ActiveInfo


class CmeView(DailyView):
    def __init__(self, flavor):
        DailyView.__init__(self, Active, CmeActives, flavor)

    def new_active(self, platform, model_launcher):
        active_name = QLineEdit()
        active_name.setPlaceholderText("Active Name")

        archive_file, archive_file_l = searchable_with_mark('Section', Active.get_archive_files(model_launcher))

        expirations, expirations_w, expirations_l = expirations_layout(model_launcher)

        info = model_launcher.controller_launcher.show_pdf_helper_dialog(
            self.get_processors(), [active_name, archive_file_l, expirations_l])

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

    def config(self):
        return {'expirations_delta': -1}