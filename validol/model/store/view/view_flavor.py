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

    def get_df(self, active_info, model_launcher):
        raise NotImplementedError

    def new_active(self, platform, model_launcher, controller_launcher):
        pass

    def remove_active(self, active_info, model_launcher):
        pass