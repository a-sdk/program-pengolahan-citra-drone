from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, 
    QFileDialog, QMessageBox, QProgressBar,
    QProgressDialog,
)
from gui.viewer import Viewer
from gui.layer_panel import LayerPanel
from gui.dialog_disease import DiseasePredictDialog
from gui.worker import Worker
from app.controller import AnalysisController
from app.result_model import AnalysisResult
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

        self.layer_panel = LayerPanel(self.layerPanel, self.viewer)
        layer_layout = QVBoxLayout(self.layerPanel)
        layer_layout.setContentsMargins(0, 0, 0, 0)
        layer_layout.addWidget(self.layer_panel)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)
    
        self.controller = AnalysisController()
        self._setup_icons()
        self._setup_statusbar()
        self.statusBar().showMessage("Ready")
        self.statusBar().addPermanentWidget(self.progress_bar)
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

        self.layer_panel.tree.setIconSize(QSize(24, 24))

    def _setup_statusbar(self):
        self.coord_label = QLabel("X: -, Y: -")
        self.statusBar().addPermanentWidget(self.coord_label)
        
    def _setup_progress_dialog(self):
        self.pd = QProgressDialog("Processing...", "Cancel", 0, 100, self)
        self.pd.setWindowTitle("Processing file")
        self.pd.setWindowModality(Qt.WindowModal)
        self.pd.setMinimumDuration(0)
        self.pd.setValue(0)

    def handle_progress_dialog(self, val, msg):
        self.pd.setValue(val)
        self.pd.setLabelText(msg)

    def update_coord_label(self, x, y):
        self.coord_label.setText(f"X: {x:.2f}, Y: {y:.2f}")

    def update_status_bar(self, file_name):
        self.statusBar().showMessage(f"Memuat: {file_name}...", 3000)

    def _connect_signals(self):
        logger.info("Sinyal Action terhubung")
        self.layer_panel.fileLoaded.connect(self.update_status_bar)
        self.action_open_shp.triggered.connect(self.open_shp_file)
        self.action_open_img.triggered.connect(self.open_img_file)
        self.actionExit.triggered.connect(self.handle_exit)
        self.action_disease_predict.triggered.connect(self.run_disease_analysis)

    def open_img_file(self):
        logger.info("Action: open_img ditekan")
        path, _ = QFileDialog.getOpenFileName(
            self, "Pilih Citra", "", "GeoTIFF (*.tif *.tiff);;Images (*.jpg *.png)"
        )
        if path:
            self.layer_panel.add_layer(path)

    def open_shp_file(self):
        logger.info("Action: open_shp ditekan")
        path, _ = QFileDialog.getOpenFileName(self, "Pilih Shapefile", "", "Shapefile (*.shp)")
        
        if path:      
            self.layer_panel.add_layer(path)

    def update_progress_bar(self, value, msg):
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(value)
            self.progress_bar.setVisible(value > 0 and value < 100)

        self.statusBar().showMessage(msg, 1000*60*10) 
        logger.info(f"Progress {value}% - {msg}")

    def on_analysis_finished(self, result: AnalysisResult):
        self.pd.close()
        if not os.path.exists(result.maps[0]):
            self.show_error_msg(f"Hasil tidak ditemukan")
            return
        
        for file in result.maps:
            try:
                self.layer_panel.add_layer(file)
            except Exception as e:
                self.show_error_msg(f"Gagal memuat hasil: {str(e)}")

    def show_error_msg(self, error_msg):
        self.pd.close()
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(False) 

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("ERROR")
        msg.setText("An error occured")
        msg.setInformativeText(str(error_msg)) 
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def run_disease_analysis(self):
        logger.info("action_disease_predict ditekan")
        dialog = DiseasePredictDialog(self)
        
        if dialog.exec_():
            tif, shp, out = dialog.get_values()
            # Menambah tif ke layer panel
            self.layer_panel.add_layer(tif)
            # Menambah shp ke layer panel
            self.layer_panel.add_layer(shp)
            # Inisiasi worker thread
            self.worker = Worker(self.controller, tif, shp, out)
            # Inisiasi progress dialog
            self._setup_progress_dialog()
            # Menghubungkan sinyal worker ke progress dialog
            self.worker.progress_signal.connect(self.handle_progress_dialog)
            self.worker.progress_signal.connect(self.update_progress_bar)
            self.worker.finished_signal.connect(self.on_analysis_finished)
            self.worker.error_signal.connect(self.show_error_msg)
            # Menghubungkan tombol 'cancel'
            self.pd.canceled.connect(self.worker.requestInterruption)
            self.worker.start()
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.statusBar().showMessage("Ready")

    def handle_exit(self):
        logger.info("Action: exit ditekan")
        reply = QMessageBox.question(self, 'Exit', 'Are you sure?', 
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            QApplication.instance().quit() 

    