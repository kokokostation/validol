from PyQt5.QtWidgets import QSystemTrayIcon, QMenu

from validol.view.view_element import ViewElement


class MySystemTrayIcon(ViewElement, QSystemTrayIcon):
    def __init__(self, icon, controller_launcher, model_launcher):
        QSystemTrayIcon.__init__(self, icon)
        ViewElement.__init__(self, controller_launcher, model_launcher)

        self.menu = QMenu()
        self.menu.addAction("Quit", self.controller_launcher.quit)

        self.setContextMenu(self.menu)

        self.activated.connect(self.on_activated)

        self.setToolTip('Validol')

        self.show()

    def on_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.controller_launcher.show_main_window()
