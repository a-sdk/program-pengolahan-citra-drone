from pathlib import Path
import sys
import json

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
    TEMP = BASE_DIR / "temp"

    @staticmethod
    def ensure_runtime_dirs():

        dirs = [
            AppPaths.RUNTIME,
            AppPaths.MODELS,
            AppPaths.SCALERS,
            AppPaths.CONFIG,
            AppPaths.CACHE,
            AppPaths.LOGS,
            AppPaths.TEMP
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
    def models(filename=""):
        return AppPaths.MODELS / filename
    
    @staticmethod
    def scalers(filename=""):
        return AppPaths.SCALERS / filename
    
    @staticmethod
    def ui(filename=""):
        return AppPaths.UI / filename
    

class ModelRegistry:

    @staticmethod
    def load_config():

        with open(
            AppPaths.CONFIG / "models.json",
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)
        
    @staticmethod
    def model_path(name):

        config = ModelRegistry.load_config()

        relative = (
            config["models"]
            [name]
            ["path"]
        )

        return (
            AppPaths.MODELS
            / relative
        )
    
    @staticmethod
    def scaler_path(name):

        config = ModelRegistry.load_config()

        relative = (
            config["scalers"]
            [name]
            ["path"]
        )

        return (
            AppPaths.SCALERS
            / relative
        )
    
class InfoRegistry:

    @staticmethod
    def load_config():

        with open(
            AppPaths.CONFIG / "info.json",
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)
        
    @staticmethod
    def get_info(name, key):

        config = InfoRegistry.load_config()

        recom = (
            config["info"]
            [name]
            [key]
        )

        return recom
    
    @staticmethod
    def get_legend(name):

        config = InfoRegistry.load_config()

        legend = (
            config["legend"]
            [name]
        )

        return legend