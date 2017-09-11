from sqlalchemy import Column, String

from validol.model.store.structures.multiple_active.multiple_actives import MultipleActiveView, \
    MultipleActives
from validol.model.store.structures.structure import Base, JSONCodec
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

        df, _ = ResourceManager(model_launcher).prepare_actives(self.info, pure_actives=True)

        return df

    @staticmethod
    def get_df(model_launcher, active):
        obj = MultipleActives(model_launcher, GluedActive).read_by_name(active)

        return obj.prepare_df(model_launcher)


class GluedActiveView(MultipleActiveView):
    def __init__(self):
        MultipleActiveView.__init__(self, "glued_active", GluedActive)

    def get_df(self, active_info, model_launcher):
        return GluedActive.get_df(model_launcher, active_info.active)
