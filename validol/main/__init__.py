import sys
import traceback

from validol.controller.telegram_notifier import TelegramNotifier
from validol.controller.launcher import ControllerLauncher


def exchook(*args):
    message = ''.join(traceback.format_exception(*args))
    TelegramNotifier().notify(message)
    sys.stderr.write(message)

    sys.exit(1)


def main():
    sys.excepthook = exchook

    cl = ControllerLauncher()

    cl.event_loop()


if __name__ == '__main__':
    main()
