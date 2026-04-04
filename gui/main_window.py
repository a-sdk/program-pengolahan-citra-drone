from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize
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

        self.setWindowTitle("Multispectral Image Processing Program")
        self.setWindowIcon(QIcon("assets/icon/edit-image.png"))
        self.viewer = Viewer()
        viewer_layout = QVBoxLayout(self.viewerPanel)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.addWidget(self.viewer)

        self.layers = LayerPanel(self.layerPanel, self.viewer)
        layer_layout = QVBoxLayout(self.layerPanel)
        layer_layout.setContentsMargins(0, 0, 0, 0)
        layer_layout.addWidget(self.layers)

        self._setup_icons()
        self._setup_statusbar()
        self.statusBar().showMessage("Siap menerima data...")
        self._connect_signals()
        self.viewer.mouseMoved.connect(self.update_coord_label)
        self.viewer.fit_to_view()

    def _setup_icons(self):
        icon_tif = QIcon("assets/icon/add_img.png")
        icon_shp = QIcon("assets/icon/poly.png")
        icon_open = QIcon("assets/icon/folder.png")
        icon_exit = QIcon("assets/icon/exit.png")
        icon_model = QIcon("assets/icon/deep-learning.png")
        icon_disease = QIcon("assets/icon/virus.png")
        icon_mineral = QIcon("assets/icon/nutrients.png")
        icon_water = QIcon("assets/icon/drop.png")
        self.menuOpen.setIcon(icon_open)
        self.action_open_img.setIcon(icon_tif)
        self.action_open_shp.setIcon(icon_shp)
        self.actionExit.setIcon(icon_exit)
        self.menuModel.setIcon(icon_model)
        self.action_nutrient_predict.setIcon(icon_mineral)
        self.action_water_predict.setIcon(icon_water)
        self.action_disease_predict.setIcon(icon_disease)

        self.layers.tree.setIconSize(QSize(24, 24))

    def _setup_statusbar(self):
        self.coord_label = QLabel("X: -, Y: -")
        self.statusBar().addPermanentWidget(self.coord_label)
        
    def update_coord_label(self, x, y):
        self.coord_label.setText(f"X: {x:.2f}, Y: {y:.2f}")

    def _connect_signals(self):
        logger.info("Sinyal Action terhubung")
        self.action_open_shp.triggered.connect(self.open_shp_file)
        self.action_open_img.triggered.connect(self.open_img_file)
        self.actionExit.triggered.connect(self.handle_exit)

    def open_img_file(self):
        logger.info("Action: open_img berhasil")
        path, _ = QFileDialog.getOpenFileName(
            self, "Pilih Citra", "", "GeoTIFF (*.tif *.tiff);;Images (*.jpg *.png)"
        )
        if path:
            layer_id = self.viewer.add_raster(path)
            file_name = os.path.basename(path)
            self.layers.add_input_layer(file_name, layer_id)
            self.statusBar().showMessage(f"Memuat Citra: {file_name}", 3000)

    def open_shp_file(self):
        logger.info("Action: open_shp berhasil")
        path, _ = QFileDialog.getOpenFileName(self, "Pilih Shapefile", "", "Shapefile (*.shp)")
        
        if path:      
            layer_id = self.viewer.add_shapefile(path)
            file_name = os.path.basename(path)
            self.layers.add_input_layer(file_name, layer_id)
            self.statusBar().showMessage(f"Memuat Vektor: {file_name}", 3000)

    def handle_exit(self):
        logger.info("Action: exit ditekan")
        reply = QMessageBox.question(self, 'Exit', 'Are you sure?', 
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            QApplication.instance().quit() 
    