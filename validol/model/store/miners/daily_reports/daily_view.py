from validol.model.store.view.view_flavor import ViewFlavor
from validol.model.store.miners.weekly_reports.flavor import Platforms


class DailyView(ViewFlavor):
    def __init__(self, active_cls, actives_cls):
        self.active_cls = active_cls
        self.actives_cls = actives_cls

    def name(self):
        return self.active_cls.FLAVOR

    def platforms(self, model_launcher):
        return Platforms(model_launcher, self.active_cls.FLAVOR).get_platforms()

    def actives(self, platform, model_launcher):
        return self.actives_cls(model_launcher).get_actives(platform)

    def active_flavors(self, platform, active, model_launcher):
        return self.active_cls(model_launcher, platform, active).get_flavors()

    def get_df(self, active_info, model_launcher):
        return self.active_cls(model_launcher, active_info.platform, active_info.active)\
            .get_flavor(active_info.active_flavor)

    def get_full_df(self, active_info, model_launcher):
        return self.active_cls(model_launcher, active_info.platform, active_info.active).read_df()

    def remove_active(self, active_info, model_launcher):
        model_launcher.remove_pdf_helper(active_info)

        self.active_cls(model_launcher, active_info.platform, active_info.active).drop()
        self.actives_cls(model_launcher).remove_active(active_info)


def active_df_tolist(df):
    return ['{} - {} - {}'.format(item.PlatformCode, item.ActiveCode, item.ActiveName)
            for _, item in df.iterrows()]