from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QFileDialog
from PyQt5 import uic
import os
import logging

logger = logging.getLogger(__name__)

class DiseasePredictDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        uic.loadUi("ui/dialog_disease.ui", self)

        self.setWindowTitle("Disease Detection")
        self.setWindowIcon(QIcon("assets/icon/virus.png"))
        self.btn_browse_tif.clicked.connect(self._handle_browse_tif)
        self.btn_browse_shp.clicked.connect(self._handle_browse_shp)
        self.btn_browse_out.clicked.connect(self._handle_browse_out)

    def _handle_browse_tif(self):
        logger.info("btn_browse_tif ditekan")
        path, _ = QFileDialog.getOpenFileName(self, "Pilih Citra", "", "Raster (*.tif *.tiff)")
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