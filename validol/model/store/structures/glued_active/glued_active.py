import pandas as pd

from validol.model.store.structures.structure import Structure, Base, JSONCodec
from sqlalchemy import Column, String


def pre_dump(info):
    return [[x[0].name()] + x[1:] for x in info]


def post_load(info):
    from validol.model.store.view.view_flavors import VIEW_FLAVORS_MAP

    return [[VIEW_FLAVORS_MAP[x[0]]] + x[1:] for x in info]


class GluedActive(Base):
    __tablename__ = "glued_actives"
    name = Column(String, primary_key=True)
    info = Column(JSONCodec(pre_dump=pre_dump, post_load=post_load))

    def __init__(self, name, info):
        self.name = name
        self.info = info

    def prepare_df(self, model_launcher):
        from validol.model.resource_manager.resource_manager import ResourceManager

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