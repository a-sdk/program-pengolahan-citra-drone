import sys
import os
import ctypes
import logging
from path_config import AppPaths
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from gui.main_window import MainWindow

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
logger = logging.getLogger(__name__)
AppPaths.ensure_runtime_dirs()
print("CWD:", os.getcwd())
print("BASE_DIR:", AppPaths.BASE_DIR)
print("RESOURCE_DIR:", AppPaths.RESOURCE_DIR)
print("UI:", AppPaths.UI)
logger.info("ASSETS:", AppPaths.ASSETS)
logger.info("CWD:", os.getcwd())
logger.info("BASE_DIR:", AppPaths.BASE_DIR)
logger.info("RESOURCE_DIR:", AppPaths.RESOURCE_DIR)
logger.info("UI:", AppPaths.UI)
logger.info("ASSETS:", AppPaths.ASSETS)
if not getattr(sys, 'frozen', False):
    venv_path = (
        AppPaths.BASE_DIR /
        ".venv" /
        "Lib" /
        "site-packages" /
        "tensorflow"
    )
    if venv_path.exists():
        os.add_dll_directory(str(venv_path))
    
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(str(AppPaths.LOGS / "app_debug.log"), mode='w'), 
        logging.StreamHandler(sys.stdout) 
    ]
)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
sys.excepthook = handle_exception

# Windows App ID
myappid = 'unpad.img_processing.ms_img.beta-0.0.1'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

# Mulai aplikasi 
logger = logging.getLogger(__name__)
logger.info("Aplikasi dibuka!")

app = QApplication(sys.argv)
window = MainWindow()
window.show()

sys.exit(app.exec_())

