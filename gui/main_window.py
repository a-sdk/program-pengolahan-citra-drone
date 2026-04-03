from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, 
    QFileDialog, QMessageBox
    )
from gui.viewer import Viewer
from gui.layer_panel import LayerPanel
import os
import logging

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/main_window.ui", self)

        self.viewer = Viewer()
        viewer_layout = QVBoxLayout(self.viewerPanel)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.addWidget(self.viewer)

        self.layers = LayerPanel(self.layerPanel, self.viewer)
        layer_layout = QVBoxLayout(self.layerPanel)
        layer_layout.setContentsMargins(0, 0, 0, 0)
        layer_layout.addWidget(self.layers)

        self._setup_statusbar()
        self.statusBar().showMessage("Siap menerima data...")
        self._connect_signals()
        self.viewer.mouseMoved.connect(self.update_coord_label)

        # layer_id = self.viewer.add_raster("aja sendiri.jpg")
        # self.layers.add_input_layer("Contoh jpg", layer_id)
        self.viewer.fit_to_view()

    def _setup_statusbar(self):
        self.coord_label = QLabel("X: -, Y: -")
        self.statusBar().addPermanentWidget(self.coord_label)
        
    def update_coord_label(self, x, y):
        self.coord_label.setText(f"X: {x:.2f}, Y: {y:.2f}")

    def load_shp(self):
        path = self.le_shp_path.text()
        if path:
            self.viewer.add_shapefile(path)
            self.layers.add_input_layer("Batas Lahan", path)


    def _connect_signals(self):
        logger.info("Sinyal Action terhubung")
        self.action_open_shp.triggered.connect(self.pilih_file_shp)
        self.action_open_img.triggered.connect(self.pilih_file_tif)
        self.actionExit.triggered.connect(self.handle_exit)

    
    def pilih_file_tif(self):
        logger.info("Aksi buka img berhasil")
        path, _ = QFileDialog.getOpenFileName(
            self, "Buka Citra Drone", "", "GeoTIFF (*.tif *.tiff);;Images (*.jpg *.png)"
        )
        if path:
            layer_id = self.viewer.add_raster(path)
            file_name = os.path.basename(path)
            self.layers.add_input_layer(file_name, layer_id)
            self.statusBar().showMessage(f"Memuat Citra: {file_name}", 3000)

    def pilih_file_shp(self):
        logger.info("Aksi buka shp berhasil")
        path, _ = QFileDialog.getOpenFileName(self, "Pilih Shapefile", "", "Shapefile (*.shp)")
        
        if path:      
            layer_id = self.viewer.add_shapefile(path)
            file_name = os.path.basename(path)
            self.layers.add_input_layer(file_name, layer_id)

            self.statusBar().showMessage(f"Memuat Vektor: {file_name}", 3000)

    def handle_exit(self):
        logger.info("Aksi exit ditekan")
        reply = QMessageBox.question(self, 'Exit', 'Are you sure?', 
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            QApplication.instance().quit() 
    