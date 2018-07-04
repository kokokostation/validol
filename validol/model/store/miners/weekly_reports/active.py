import pandas as pd

from validol.model.store.resource import Actives, ActiveResource


class WeeklyActives(Actives):
    def __init__(self, model_launcher, flavor):
        Actives.__init__(self, model_launcher.main_dbh, flavor)


class Active(ActiveResource):
    def __init__(self, model_launcher, flavor, platform_code, active_name, update_info=None):
        ActiveResource.__init__(self,
                                flavor["schema"],
                                model_launcher,
                                platform_code,
                                active_name,
                                flavor["name"],
                                actives_cls=WeeklyActives)

        self.update_info = pd.DataFrame() if update_info is None else update_info

    def initial_fill(self):
        return self.update_info

    def fill(self, first, last):
        return self.update_info[(first <= self.update_info.Date) &
                                (self.update_info.Date <= last)]
