from sqlalchemy import Column, String, Boolean, DateTime
from croniter import croniter

from validol.model.store.structures.structure import NamedStructure, Base, with_session


class Scheduler(Base):
    __tablename__ = 'schedulers'

    name = Column(String, primary_key=True)
    cron = Column(String, primary_key=True)
    working = Column(Boolean)
    next_time = Column(DateTime)

    def __init__(self, name, cron, working, next_time):
        self.name = name
        self.cron = cron
        self.working = working
        self.next_time = next_time


class Schedulers(NamedStructure):
    def __init__(self, model_launcher):
        NamedStructure.__init__(self, Scheduler, model_launcher)

    @staticmethod
    def get_cond(scheduler):
        return (Scheduler.name == scheduler.name) & \
               (Scheduler.cron == scheduler.cron)

    @staticmethod
    def get_scheduler(session, scheduler):
        return session.query(Scheduler).filter(Schedulers.get_cond(scheduler)).one()

    @with_session
    def switch(self, session, scheduler):
        dbo = Schedulers.get_scheduler(session, scheduler)
        dbo.working = not dbo.working

        if dbo.working:
            dbo.next_time = None

    @with_session
    def set_next_time(self, session, scheduler, next_time):
        dbo = Schedulers.get_scheduler(session, scheduler)
        dbo.next_time = next_time

    def write_scheduler(self, name, cron, working):
        if croniter.is_valid(cron):
            self.write(Scheduler(name, cron, working, None))

    def remove_scheduler(self, scheduler):
        self.remove_by_pred(Schedulers.get_cond(scheduler))