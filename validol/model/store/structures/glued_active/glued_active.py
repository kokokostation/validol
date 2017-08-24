import pandas as pd
from sqlalchemy import Column, String

from validol.model.store.structures.structure import Structure, Base, JSONCodec
from validol.model.store.view.active_info import ActiveInfoSchema


class GluedActive(Base):
    __tablename__ = "glued_actives"
    name = Column(String, primary_key=True)
    info = Column(JSONCodec(ActiveInfoSchema(many=True)))

    def __init__(self, name, info):
        self.name = name
        self.info = info

    def prepare_df(self, model_launcher):
        from validol.model.resource_manager.resource_manager import ResourceManager

        df, _ = ResourceManager(model_launcher).prepare_actives(self.info)

        return df

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