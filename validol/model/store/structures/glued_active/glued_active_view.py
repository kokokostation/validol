from validol.model.store.view.view_flavor import ViewFlavor
from validol.model.store.structures.glued_active.glued_active import GluedActives, GluedActive

import pandas as pd


class GluedActiveView(ViewFlavor):
    def name(self):
        return "GLUED_ACTIVE"

    def platforms(self, model_launcher):
        return pd.DataFrame([["GA", "Glued actives"]], columns=["PlatformCode", "PlatformName"])

    def actives(self, platform, model_launcher):
        return GluedActives(model_launcher).get_actives()

    def get_df(self, platform, active, model_launcher):
        return GluedActive.get_df(model_launcher, active)