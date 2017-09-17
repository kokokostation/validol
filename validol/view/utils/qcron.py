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

        self.next_event = None

        self.set_qtimer()

    def act(self):
        self.set_qtimer()
        self.action()

    def set_qtimer(self):
        self.next_event = self.iter.get_next(dt.datetime)
        self.qtimer.setInterval((self.next_event - dt.datetime.now()).seconds * 1000)
        self.qtimer.start()

    def stop(self):
        self.qtimer.stop()