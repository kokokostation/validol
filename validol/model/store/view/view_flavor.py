import pandas as pd
from functools import partial

from validol.model.store.view.active_info import ActiveInfo


class ViewFlavor:
    def platforms(self, model_launcher):
        raise NotImplementedError

    def actives(self, platform, model_launcher):
        raise NotImplementedError

    def active_flavors(self, platform, active, model_launcher):
        return pd.DataFrame([None], columns=['active_flavor'])

    def name(self):
        raise NotImplementedError

    def get_df(self, active_info, model_launcher):
        raise NotImplementedError

    def new_active(self, platform, model_launcher, controller_launcher):
        pass

    def remove_active(self, active_info, model_launcher):
        pass

    def remove_active_data(self, active_info, model_launcher):
        pass

    def all_actives(self, model_launcher, with_flavors=True):
        result = []

        for index, platform in self.platforms(model_launcher).iterrows():
            for index, active in self.actives(platform.PlatformCode, model_launcher).iterrows():
                if with_flavors:
                    afs_getter = self.active_flavors
                else:
                    afs_getter = partial(ViewFlavor.active_flavors, self)

                afs = afs_getter(platform.PlatformCode, active.ActiveName, model_launcher)

                for index, active_flavor in afs.iterrows():
                    result.append(ActiveInfo(self,
                                             platform.PlatformCode,
                                             active.ActiveName,
                                             active_flavor.active_flavor))

        return result