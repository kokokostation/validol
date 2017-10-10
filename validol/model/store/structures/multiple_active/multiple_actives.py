import pandas as pd

from validol.model.store.structures.structure import NamedStructure
from validol.model.store.view.view_flavor import ViewFlavor


class MultipleActives(NamedStructure):
    def __init__(self, model_launcher, active_cls):
        NamedStructure.__init__(self, active_cls, model_launcher)

    def get_actives(self):
        return pd.DataFrame([active.name for active in self.read()], columns=["ActiveName"])

    def write_active(self, name, info):
        self.write(self.klass(name, info))


class MultipleActiveView(ViewFlavor):
    def __init__(self, flavor, active_cls):
        self.flavor = flavor
        self.active_cls = active_cls

    def name(self):
        return self.flavor

    def platforms(self, model_launcher):
        return pd.DataFrame([["CODE", self.flavor]],
                            columns=["PlatformCode", "PlatformName"])

    def actives(self, platform, model_launcher):
        return MultipleActives(model_launcher, self.active_cls).get_actives()

    def new_active(self, platform, model_launcher):
        chosen_actives = model_launcher.controller_launcher.get_chosen_actives()

        if not chosen_actives:
            model_launcher.controller_launcher.display_error('No actives', 'You need to pick at least 1 active')
            return

        name = model_launcher.controller_launcher.ask_name()
        if name is not None:
            MultipleActives(model_launcher, self.active_cls)\
                .write_active(name, chosen_actives)

    def remove_active(self, ai, model_launcher):
        MultipleActives(model_launcher, self.active_cls).remove_by_name(ai.active)