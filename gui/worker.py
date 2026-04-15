from PyQt5.QtCore import QThread, pyqtSignal

class Worker(QThread):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)

    def __init__(self, controller, tif, shp, out):
        super().__init__()
        self.controller = controller
        self.tif = tif
        self.shp = shp
        self.out = out

    def run(self):
        hooks = {
            "on_progress": lambda val, msg: self.progress_signal.emit(val, msg),
            "on_error": lambda err: self.error_signal.emit(err),
            "on_finished": lambda result: self.finished_signal.emit(result), 
            "check_interruption": lambda: self.isInterruptionRequested()
        }
        self.controller.run(self.tif, self.shp, self.out, hooks)