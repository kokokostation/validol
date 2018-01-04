class ViewElement:
    def __init__(self, controller_launcher, model_launcher):
        self.controller_launcher = controller_launcher
        self.model_launcher = model_launcher

    def closeEvent(self, qce):
        self.controller_launcher.free_window(self)
