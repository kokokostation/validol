import requests

from validol.view.utils.qcron import QCron


class SchedulerQCron(QCron):
    def __init__(self, scheduler, model_launcher, action):
        QCron.__init__(self, scheduler.cron, action)

        self.model_launcher = model_launcher
        self.scheduler = scheduler

    def set_qtimer(self):
        super().set_qtimer()
        self.model_launcher.set_scheduler_next_time(self.scheduler, self.next_event)


class QCronManager:
    def __init__(self, model_launcher, view_launcher):
        self.model_launcher = model_launcher
        self.view_launcher = view_launcher

        self.qcrons = []
        self.schedulers = []
        self.update_needed = set()

    def refresh(self):
        schedulers = [scheduler for scheduler in self.model_launcher.read_schedulers()
                      if scheduler.working]

        update_manager = self.model_launcher.get_update_manager()

        for qcron in self.qcrons:
            qcron.stop()

        self.qcrons = [SchedulerQCron(scheduler, self.model_launcher, self.update_wrapper(update_manager, scheduler.name))
                       for scheduler in schedulers]

        for qcron in self.qcrons:
            if qcron.next_event != qcron.scheduler.next_time:
                self.update_needed.add(qcron.scheduler.name)

        self.refresh_main_window()

    def register_update(self, source):
        if source in self.update_needed:
            self.update_needed.remove(source)

        self.refresh_main_window()

    def refresh_main_window(self):
        self.view_launcher.set_update_missed(self.update_needed != [])

    def update_wrapper(self, update_manager, source):
        def shot():
            if update_manager.verbose(source):
                self.view_launcher.notify('Update of {} started'.format(source))

            try:
                results = update_manager.update_source(source)
            except requests.exceptions.ConnectionError:
                if update_manager.verbose(source):
                    self.view_launcher.notify('Update of {} failed due to network error'.format(source))
                return

            if update_manager.verbose(source):
                self.view_launcher.notify_update(results)

        return shot

    def update_missed(self):
        update_manager = self.model_launcher.get_update_manager()

        for source in list(self.update_needed):
            self.update_wrapper(update_manager, source)()