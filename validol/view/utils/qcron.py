from croniter import croniter
import datetime as dt
from PyQt5.QtCore import QTimer


class QCron:
    def __init__(self, cron, action):
        self.action = action

        self.iter = croniter(cron, dt.datetime.now())

        self.qtimer = QTimer()
        self.qtimer.setSingleShot(True)
        self.qtimer.timeout.connect(self.act)

        self.set_qtimer()

    def act(self):
        self.action()
        self.set_qtimer()

    def set_qtimer(self):
        next_event = self.iter.get_next(dt.datetime)
        self.qtimer.setInterval((dt.datetime.now() - next_event).seconds * 1000)
        self.qtimer.start()

    def stop(self):
        self.qtimer.stop()