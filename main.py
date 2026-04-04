import sys
import os
import ctypes
import logging
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow   
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

venv_path = os.path.join(os.getcwd(), ".venv", "Lib", "site-packages", "tensorflow")
if os.path.exists(venv_path):
    os.add_dll_directory(venv_path)
    
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("app_debug.log", mode='w'), 
        logging.StreamHandler(sys.stdout) 
    ]
)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

myappid = 'unpad.img_processing.ms_img.beta-0.0.1'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
# Mulai aplikasi 
logger = logging.getLogger(__name__)
logger.info("Aplikasi dibuka!")

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())

sys.excepthook = handle_exception