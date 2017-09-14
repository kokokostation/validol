from sqlalchemy import Column, String, Boolean
from croniter import croniter

from validol.model.store.structures.structure import NamedStructure, Base, with_session


class Scheduler(Base):
    __tablename__ = 'schedulers'

    name = Column(String, primary_key=True)
    cron = Column(String, primary_key=True)
    working = Column(Boolean)

    def __init__(self, name, cron, working):
        self.name = name
        self.cron = cron
        self.working = working


class Schedulers(NamedStructure):
    def __init__(self, model_launcher):
        NamedStructure.__init__(self, Scheduler, model_launcher)

    @staticmethod
    def get_cond(scheduler):
        return (Scheduler.name == scheduler.name) & \
               (Scheduler.cron == scheduler.cron)

    @with_session
    def switch(self, session, scheduler):
        dbo = session.query(Scheduler).filter(Schedulers.get_cond(scheduler)).one()
        dbo.working = not dbo.working

    def write_scheduler(self, name, cron, working):
        if croniter.is_valid(cron):
            self.write(Scheduler(name, cron, working))

    def remove_scheduler(self, scheduler):
        self.remove_by_pred(Schedulers.get_cond(scheduler))