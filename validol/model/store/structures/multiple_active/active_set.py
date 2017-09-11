from sqlalchemy import Column, String

from validol.model.store.structures.multiple_active.multiple_actives import MultipleActiveView, \
    MultipleActives
from validol.model.store.structures.structure import Base, JSONCodec
from validol.model.store.view.active_info import ActiveInfoSchema


class ActiveSet(Base):
    __tablename__ = "active_sets"
    name = Column(String, primary_key=True)
    info = Column(JSONCodec(ActiveInfoSchema(many=True)))

    def __init__(self, name, info):
        self.name = name
        self.info = info


class ActiveSetView(MultipleActiveView):
    def __init__(self):
        MultipleActiveView.__init__(self, 'active_set', ActiveSet)

    def active_infos(self, ai, model_launcher):
        return MultipleActives(model_launcher, ActiveSet).read_by_name(ai.active).info