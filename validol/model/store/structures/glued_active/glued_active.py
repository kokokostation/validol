import pandas as pd
from sqlalchemy import Column, String

from validol.model.store.structures.structure import Structure, Base, JSONCodec
from validol.model.utils import merge_dfs_list
from validol.model.store.view.active_info import ActiveInfoSchema


class GluedActive(Base):
    __tablename__ = "glued_actives"
    name = Column(String, primary_key=True)
    info = Column(JSONCodec(ActiveInfoSchema))

    def __init__(self, name, info):
        self.name = name
        self.info = info

    def prepare_df(self, model_launcher):
        from validol.model.resource_manager.resource_manager import ResourceManager

        dfs = ResourceManager(model_launcher).prepare_actives(self.info)

        return merge_dfs_list(dfs)

    @staticmethod
    def get_df(model_launcher, active):
        obj = GluedActives(model_launcher).read_by_name(active)

        return obj.prepare_df(model_launcher)


class GluedActives(Structure):
    def __init__(self, model_launcher):
        Structure.__init__(self, GluedActive, model_launcher)

    def get_actives(self):
        return pd.DataFrame([active.name for active in self.read()], columns=["ActiveName"])

    def write_active(self, name, info):
        self.write(GluedActive(name, info))