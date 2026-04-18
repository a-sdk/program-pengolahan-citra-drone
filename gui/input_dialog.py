from PyQt5.QtWidgets import QDialog, QFileDialog
from PyQt5 import uic
import logging

logger = logging.getLogger(__name__)

class InputDialog(QDialog):
    def __init__(self, parent=None, title="", icon=None):
        super().__init__(parent)
        uic.loadUi("ui/input_dialog.ui", self)

        self.setWindowTitle(title)
        self.setWindowIcon(icon)
        self.btn_browse_tif.clicked.connect(self._handle_browse_tif)
        self.btn_browse_shp.clicked.connect(self._handle_browse_shp)
        self.btn_browse_out.clicked.connect(self._handle_browse_out)

    def _handle_browse_tif(self):
        logger.info("btn_browse_tif ditekan")
        path, _ = QFileDialog.getOpenFileName(self, "Pilih Citra", "", "GeoTiff (*.tif *.tiff)")
        if path: self.lineEdit_tif.setText(path)


    def _handle_browse_shp(self):
        logger.info("btn_browse_shp ditekan")
        path, _ = QFileDialog.getOpenFileName(self, "Pilih Shapefile", "", "Shapefile (*.shp)")
        if path: self.lineEdit_shp.setText(path)

    def _handle_browse_out(self):
        logger.info("btn_browse_out ditekan")
        path = QFileDialog.getExistingDirectory(self, "Pilih Folder Output")
        if path: self.lineEdit_out.setText(path)   

    def get_values(self):
        return (self.lineEdit_tif.text(), 
                self.lineEdit_shp.text(), 
                self.lineEdit_out.text()) 