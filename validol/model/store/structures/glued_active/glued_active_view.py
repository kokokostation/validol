from validol.model.store.view.view_flavor import ViewFlavor
from validol.model.store.structures.glued_active.glued_active import GluedActives, GluedActive

import pandas as pd


class GluedActiveView(ViewFlavor):
    def name(self):
        return "glued_active"

    def platforms(self, model_launcher):
        return pd.DataFrame([["GA", "Glued actives"]], columns=["PlatformCode", "PlatformName"])

    def actives(self, platform, model_launcher):
        return GluedActives(model_launcher).get_actives()

    def get_df(self, active_info, model_launcher):
        return GluedActive.get_df(model_launcher, active_info.active)

    def new_active(self, platform, model_launcher, controller_launcher):
        name = controller_launcher.ask_name()
        if name is not None:
            model_launcher.write_glued_active(name, controller_launcher.get_chosen_actives())

    def remove_active(self, active_info, model_launcher):
        model_launcher.remove_glued_active(active_info.active)
