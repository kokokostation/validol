import pandas as pd


class ViewFlavor:
    def platforms(self, model_launcher):
        raise NotImplementedError

    def actives(self, platform, model_launcher):
        raise NotImplementedError

    def active_flavors(self, platform, active, model_launcher):
        return pd.DataFrame()

    def name(self):
        raise NotImplementedError

    def get_df(self, platform, active, active_flavor, model_launcher):
        raise NotImplementedError

    def switch_update(self, platform, active, model_launcher):
        pass