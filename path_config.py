from pathlib import Path
import sys

class AppPaths:

    if getattr(sys, 'frozen', False):
        BASE_DIR = Path(sys.executable).resolve().parent
        RESOURCE_DIR = Path(sys._MEIPASS)
    else:
        BASE_DIR = Path(__file__).resolve().parent
        RESOURCE_DIR = BASE_DIR

    # Internal bundled resources
    APP = RESOURCE_DIR / "app"
    ASSETS = RESOURCE_DIR / "assets"
    GUI = RESOURCE_DIR / "gui"
    UI = RESOURCE_DIR / "ui"
    CORE = RESOURCE_DIR / "core"

    # External runtime data
    RUNTIME = BASE_DIR / "runtime"
    CACHE = RUNTIME / "cache"
    CONFIG = RUNTIME / "config"
    LOGS = RUNTIME / "logs"
    MODELS = RUNTIME / "models"
    SCALERS = RUNTIME / "scalers"

    @staticmethod
    def ensure_runtime_dirs():

        dirs = [
            AppPaths.RUNTIME,
            AppPaths.MODELS,
            AppPaths.SCALERS,
            AppPaths.CONFIG,
            AppPaths.CACHE,
            AppPaths.LOGS,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    # Helper
    @staticmethod
    def app(filename=""):
        return AppPaths.APP / filename
    
    @staticmethod
    def assets(filename=""):
        return AppPaths.ASSETS / filename

    @staticmethod
    def core(filename=""):
        return AppPaths.CORE / filename
    
    @staticmethod
    def gui(filename=""):
        return AppPaths.GUI / filename
    
    @staticmethod
    def runtime(filename=""):
        return AppPaths.RUNTIME / filename
    
    @staticmethod
    def ui(filename=""):
        return AppPaths.UI / filename