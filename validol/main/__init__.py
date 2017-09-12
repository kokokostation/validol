from tendo import singleton

from validol.controller.launcher import ControllerLauncher


def main():
    me = singleton.SingleInstance()

    ControllerLauncher()

if __name__ == '__main__':
    main()
