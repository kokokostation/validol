import pandas as pd

from market_graphs.model.store.structures.structure import Structure, Base
from sqlalchemy import Column, String, PickleType


class GluedActive(Base):
    __tablename__ = "glued_actives"
    name = Column(String, primary_key=True)
    info = Column(PickleType)

    def __init__(self, name, info):
        self.name = name
        self.info = info

    def prepare_df(self, model_launcher):
        from market_graphs.model.resource_manager.resource_manager import ResourceManager

        dfs = ResourceManager(model_launcher).prepare_actives(self.info)

        result = dfs[0]
        for df in dfs[1:]:
            result = GluedActive.merge_dfs(result, df)

        return result

    @staticmethod
    def merge_dfs(dfa, dfb):
        suffix = "_y"

        merged = dfa.merge(dfb, 'outer', 'Date', sort=True, suffixes=("", suffix))

        intersection = set(dfa.columns) & set(dfb.columns) - {"Date"}

        for col in intersection:
            merged[col].fillna(merged[col + suffix], inplace=True)
            del merged[col + suffix]

        return merged

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