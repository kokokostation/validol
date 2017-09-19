import requests
from PyQt5.QtCore import QTimer
import datetime as dt

from validol.view.utils.qcron import QCron


class SchedulerQCron(QCron):
    def __init__(self, scheduler, model_launcher, action):
        self.model_launcher = model_launcher
        self.scheduler = scheduler

        QCron.__init__(self, scheduler.cron, action)

    def set_qtimer(self):
        super().set_qtimer()
        self.model_launcher.set_scheduler_next_time(self.scheduler, self.next_event)


class SuspendChecker:
    def __init__(self, handler, interval=2, alarm_interval=7):
        self.handler = handler
        self.interval = interval
        self.alarm_interval = alarm_interval

        self.qtimer = QTimer()
        self.qtimer.timeout.connect(self.checker)
        self.qtimer.start(self.interval * 1000)

        self.last_timeout = dt.datetime.now()

    def checker(self):
        last_timeout = self.last_timeout
        self.last_timeout = dt.datetime.now()

        if (dt.datetime.now() - last_timeout).seconds > self.alarm_interval:
            self.handler()


class QCronManager:
    def __init__(self, model_launcher, view_launcher):
        self.model_launcher = model_launcher
        self.view_launcher = view_launcher

        self.qcrons = []
        self.schedulers = []
        self.update_needed = set()

        self.suspend_checker = SuspendChecker(self.refresh)

    def refresh(self):
        schedulers = [scheduler for scheduler in self.model_launcher.read_schedulers()
                      if scheduler.working]

        update_manager = self.model_launcher.get_update_manager()

        for qcron in self.qcrons:
            qcron.stop()

        self.qcrons = [SchedulerQCron(scheduler, self.model_launcher, self.update_wrapper(update_manager, scheduler.name))
                       for scheduler in schedulers]

        for qcron in self.qcrons:
            if qcron.scheduler.next_time != None \
                    and qcron.next_event != qcron.scheduler.next_time \
                    and update_manager.config(qcron.scheduler.name)['important']:
                self.update_needed.add(qcron.scheduler.name)

        self.refresh_main_window()

    def register_update(self, source):
        if source in self.update_needed:
            self.update_needed.remove(source)

        self.refresh_main_window()

    def refresh_main_window(self):
        self.view_launcher.set_update_missed(bool(self.update_needed))

    def update_wrapper(self, update_manager, source):
        def shot():
            if update_manager.config(source)['verbose']:
                self.view_launcher.notify('Update of {} started'.format(source))

            try:
                results = update_manager.update_source(source)
            except requests.exceptions.ConnectionError:
                if update_manager.config(source)['verbose']:
                    self.view_launcher.notify('Update of {} failed due to network error'.format(source))
                return

            if update_manager.config(source)['verbose']:
                self.view_launcher.notify_update(results)

        return shot

    def update_missed(self):
        update_manager = self.model_launcher.get_update_manager()

        for source in list(self.update_needed):
            self.update_wrapper(update_manager, source)()