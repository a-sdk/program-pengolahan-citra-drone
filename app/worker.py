from PyQt5.QtCore import QThread, pyqtSignal

class Worker(QThread):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            hooks = {
                "on_progress": lambda val, msg: self.progress_signal.emit(val, msg),
                "on_error": lambda err: self.error_signal.emit(err), 
                "check_interruption": lambda: self.isInterruptionRequested()
            }
            result = self.func(
                *self.args,
                hooks=hooks,
                **self.kwargs
            )
            self.finished_signal.emit(result)
        except  Exception as e:
            self.error_signal.emit(str(e))


class WorkerHelper:
    def __init__(self, hooks=None):
        self.hooks = hooks or {}

    def progress(self, val, msg):
        cb = self.hooks.get("on_progress")
        if cb:
            cb(val, msg)

    def error(self, msg):
        cb = self.hooks.get("on_error")
        if cb:
            cb(msg)

    def cancelled(self):
        cb = self.hooks.get("check_interruption")
        return cb() if cb else False
    


        