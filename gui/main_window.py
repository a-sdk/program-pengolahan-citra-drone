from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, 
    QFileDialog, QMessageBox, QProgressBar,
    QProgressDialog
)
from gui.viewer import Viewer
from gui.layer_panel import LayerPanel
from gui.legend_panel import LegendPanel
from gui.input_dialog import InputDialog
from gui.worker import Worker
from app.disease_controller import DiseaseAnalysis
from app.water_controller import WaterAnalysis
from app.nutrient_controller import NutrientAnalysis
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
        self.elapsed_sec = 0
        self.time_str = str(0)
        self.current_msg = "Processing..."
        self.viewer = Viewer(self.containerViewer)
        viewer_layout = QVBoxLayout(self.containerViewer)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.addWidget(self.viewer)
        # logger.info(f"Viewer panel tipe: {type(self.viewer)}, parent: {self.viewer.parent()}")

        self.layer_panel = LayerPanel(self.containerLayer, self.viewer)
        layer_layout = QVBoxLayout(self.containerLayer)
        layer_layout.setContentsMargins(0, 0, 0, 0)
        layer_layout.addWidget(self.layer_panel)
        # logger.info(f"Layer panel tipe: {type(self.layer_panel)}, parent: {self.layer_panel.parent()}")

        self.legend_panel = LegendPanel(self.containerLegend)
        legend_layout = QVBoxLayout(self.containerLegend)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.addWidget(self.legend_panel)
        # logger.info(f"Legend panel tipe: {type(self.legend_panel)}, parent: {self.legend_panel.parent()}")

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)
    
        self.disease_ctrl = DiseaseAnalysis()
        self.water_ctrl = WaterAnalysis()
        self.nutrient_ctrl = NutrientAnalysis()
        self._setup_icons()
        self._setup_statusbar()
        self.statusBar().showMessage("Ready")
        self.statusBar().addPermanentWidget(self.progress_bar)
        self._connect_signals()
        self.viewer.mouseMoved.connect(self.update_coord_label)
        self.viewer.fit_to_view()

        self.dockLayers.setWindowTitle("Layers")
        self.action_layer_panel.setCheckable(True)
        self.action_layer_panel.toggled.connect(self.dockLayers.setVisible)
        self.dockLayers.visibilityChanged.connect(self.action_layer_panel.setChecked)

        self.dockLegend.setWindowTitle("Legend")
        self.action_legend_panel.setCheckable(True)
        self.action_legend_panel.toggled.connect(self.dockLegend.setVisible)
        self.dockLegend.visibilityChanged.connect(self.action_legend_panel.setChecked)

        self.dockLayers.show()
        self.action_layer_panel.setChecked(True)
        self.dockLegend.hide()
        self.action_legend_panel.setChecked(False)
        

    def _setup_icons(self):
        icon_tif = QIcon("assets/icon/add_img.png")
        icon_shp = QIcon("assets/icon/poly.png")
        icon_open = QIcon("assets/icon/folder.png")
        icon_exit = QIcon("assets/icon/exit.png")
        icon_model = QIcon("assets/icon/deep-learning.png")
        self.icon_disease = QIcon("assets/icon/virus.png")
        self.icon_mineral = QIcon("assets/icon/nutrients.png")
        self.icon_water = QIcon("assets/icon/drop.png")
        icon_hand = QIcon("assets/icon/hand.png")
        icon_zoom_in = QIcon("assets/icon/zoom-in.png")
        icon_zoom_out = QIcon("assets/icon/zoom-out.png")
        icon_fit_to_view = QIcon("assets/icon/width.png")
        self.menuOpen.setIcon(icon_open)
        self.action_open_img.setIcon(icon_tif)
        self.action_open_shp.setIcon(icon_shp)
        self.action_exit.setIcon(icon_exit)
        self.action_pan.setIcon(icon_hand)
        self.action_zoom_in.setIcon(icon_zoom_in)
        self.action_zoom_out.setIcon(icon_zoom_out)
        self.action_fit_to_view.setIcon(icon_fit_to_view)
        self.menuModel.setIcon(icon_model)
        self.action_nutrient_predict.setIcon(self.icon_mineral)
        self.action_water_predict.setIcon(self.icon_water)
        self.action_disease_predict.setIcon(self.icon_disease)
        self.layer_panel.tree.setIconSize(QSize(24, 24))

    def _setup_statusbar(self):
        self.coord_label = QLabel("X: -, Y: -")
        self.statusBar().addPermanentWidget(self.coord_label)

    def _setup_progress_dialog(self):
        self.pd = QProgressDialog(self.current_msg, "Cancel", 0, 100, self)
        self.pd.setWindowTitle("Please wait")
        self.pd.setWindowModality(Qt.WindowModal)
        self.pd.setMinimumDuration(0)
        self.pd.setValue(0)
        self.elapsed_sec = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_timer_label)
        self.timer.start(1000) # ms

    def handle_progress_dialog(self, val, msg):
        self.current_msg = msg
        self.pd.setValue(val)
        self.pd.setLabelText(f"{msg}\nElapsed: {self.time_str}")

    def _update_timer_label(self):
        self.elapsed_sec += 1
        self.mins = self.elapsed_sec // 60
        self.secs = self.elapsed_sec % 60
        self.time_str = f"{self.mins}m {self.secs}s" if self.mins > 0 else f"{self.secs}s"
        self.pd.setLabelText(f"{self.current_msg}\nElapsed: {self.time_str}")

    def update_coord_label(self, x, y):
        self.coord_label.setText(f"X: {x:.2f}, Y: {y:.2f}")

    def update_status_bar(self, file_name):
        self.statusBar().showMessage(f"Memuat: {file_name}...", 3000)

    def _connect_signals(self):
        logger.info("Sinyal Action terhubung")
        self.layer_panel.fileLoaded.connect(self.update_status_bar)
        self.layer_panel.layerSelected.connect(self.update_legend_from_layer)
        self.action_open_shp.triggered.connect(self.open_vector_file)
        self.action_open_img.triggered.connect(self.open_img_file)
        self.action_exit.triggered.connect(self.handle_exit)
        self.action_pan.toggled.connect(self.viewer.set_pan_mode)
        self.action_zoom_in.triggered.connect(self.viewer.zoom_in)
        self.action_zoom_out.triggered.connect(self.viewer.zoom_out)
        self.action_fit_to_view.triggered.connect(self.viewer.fit_to_view)
        self.action_disease_predict.triggered.connect(self.run_disease_prediction)
        self.action_water_predict.triggered.connect(self.run_water_prediction)
        self.action_nutrient_predict.triggered.connect(self.run_nutrient_prediction)
        # self.action_debug.triggered.connect(self.simulate_finished)

    def open_img_file(self):
        logger.info("Action: open_img ditekan")
        path, _ = QFileDialog.getOpenFileName(
            self, "Pilih Citra", "", "GeoTIFF (*.tif *.tiff);;Images (*.jpg *.png)"
        )
        if path:
            self.layer_panel.add_layer(path)

    def open_vector_file(self):
        logger.info("Action: open_shp ditekan")
        path, _ = QFileDialog.getOpenFileName(self, "Pilih Vektor", "", "Shapefile (*.shp);;Geopackage (*.gpkg)")
        
        if path:      
            self.layer_panel.add_layer(path)
    
    def update_legend_from_layer(self, layer_id):
        logger.info("Legenda diperbarui!")
        info = (
            self.viewer.raster_info.get(layer_id)
            or
            self.viewer.vector_info.get(layer_id)
        )

        if not info:
            self.legend_panel.clear()
            return

        legend = None
        stats = None

        
        if info.get("type") == "gpkg":
            legend, stats = self.viewer.read_gpkg_metadata(
                info["path"],
                info["layer_name"]
            )
        else:
            legend = info.get("legend")
            stats = info.get("stats")

        if not legend and not stats:
            self.legend_panel.clear()
            return

        if legend:
            self.legend_panel.set_legend(legend)

        if stats:
            self.legend_panel.set_info(stats)

        self.dockLegend.show()

    def update_progress_bar(self, value, msg):
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(value)
            self.progress_bar.setVisible(value > 0 and value < 100)

        self.statusBar().showMessage(msg, 1000*60*10) 
        logger.info(f"Progress {value}% - {msg}")

    def run_analysis(self, controller, tif, shp, out):
        # Menambah tif ke layer panel
        self.layer_panel.add_layer(tif)
        # Menambah shp ke layer panel
        self.layer_panel.add_layer(shp)
        # Inisiasi worker thread
        self.worker = Worker(controller, tif, shp, out)
        # Inisiasi progress dialog
        self._setup_progress_dialog()
        # Menghubungkan sinyal worker ke progress dialog
        self.worker.progress_signal.connect(self.handle_progress_dialog)
        self.worker.progress_signal.connect(self.update_progress_bar)
        self.worker.finished_signal.connect(self.on_analysis_finished)
        self.worker.error_signal.connect(self.show_error_msg)
        # Menghubungkan tombol 'cancel'
        self.pd.canceled.connect(self.worker.requestInterruption)
        # Memulai proses
        self.worker.start()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("Ready")

    def on_analysis_finished(self, result: AnalysisResult):
        # Menutup timer dan dialog progress
        self.timer.stop()
        self.pd.close()
        # Muncul dialog selesai
        self.show_finished()
        # Membuka file hasil prediksi
        if isinstance(result.prediction_path, list):
            if not os.path.exists(result.prediction_path[0]):
                self.show_error_msg(f"File not found.")
                return
            for file in result.prediction_path:
                try:
                    self.layer_panel.add_layer(file, isPrediction=True)
                except Exception as e:
                    self.show_error_msg(f"{str(e)}")
        else:
            try:
                self.layer_panel.add_layer(result.prediction_path)
            except Exception as e:
                self.show_error_msg(f"{str(e)}")

    def show_finished(self):
        self.timer.stop()
        self.pd.close()
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(False)
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Finished")
        msg.setText("All process finished.")
        msg.setInformativeText(f"Duration: {self.time_str}") 
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def show_error_msg(self, error_msg):
        self.timer.stop()
        self.pd.close()
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(False) 
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("ERROR")
        msg.setText("An error occured")
        msg.setInformativeText(str(error_msg)) 
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def run_disease_prediction(self):
        logger.info("action_disease_predict ditekan")
        dialog = InputDialog(self, title="Disease Detection", icon=self.icon_disease)
        if dialog.exec_():
            tif, shp, out = dialog.get_values()
            self.run_analysis(self.disease_ctrl, tif, shp, out)

    def run_water_prediction(self):
        logger.info("action_water_predict ditekan")
        dialog = InputDialog(self, title="Water Availability", icon=self.icon_water)
        if dialog.exec_():
            tif, shp, out = dialog.get_values()
            self.run_analysis(self.water_ctrl, tif, shp, out)

    def run_nutrient_prediction(self):
        logger.info("action_disease_predict ditekan")
        dialog = InputDialog(self, title="Nutrient Availability", icon=self.icon_mineral)
        if dialog.exec_():
            tif, shp, out = dialog.get_values()
            self.run_analysis(self.nutrient_ctrl, tif, shp, out)

    def handle_exit(self):
        logger.info("Action: exit ditekan")
        reply = QMessageBox.question(self, 'Exit', 'Are you sure?', 
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            QApplication.instance().quit() 

    # DEBUGGING FINISH
    def simulate_finished(self):
        from app.result_model import AnalysisResult

        fake = AnalysisResult()
        fake.prediction_path = r"C:\Users\acer_\Documents\Orthomosaic\tes aplikasi\Lahan percobaan\Hasil_Prediksi\Sebaran_Petak\Hasil_Prediksi.gpkg"
        # fake.prediction_path = [
        #     "C:/Users/acer_/Documents/Orthomosaic/tes aplikasi/Lahan percobaan/Hasil_Prediksi/Sebaran_Rumpun/peta_sebaran_penyakit_bercak cokelat.tif",
        #     "C:/Users/acer_/Documents/Orthomosaic/tes aplikasi/Lahan percobaan/Hasil_Prediksi/Sebaran_Rumpun/peta_sebaran_penyakit_bercak sempit.tif",
        #     "C:/Users/acer_/Documents/Orthomosaic/tes aplikasi/Lahan percobaan/Hasil_Prediksi/Sebaran_Rumpun/peta_sebaran_penyakit_blas.tif",
        #     "C:/Users/acer_/Documents/Orthomosaic/tes aplikasi/Lahan percobaan/Hasil_Prediksi/Sebaran_Rumpun/peta_sebaran_penyakit_hdb.tif"
        # ]
        fake.statistic = {
            'Healthy': 5.29, 
            'Low': 0.0, 
            'Mild': 0.41, 
            'Severe': 94.3, 
            'rekomendasi': 'High severity level, immediate action required!'
        }

        fake.legend = {
            1: {"label": "Healthy", "color": (0,128,0)},
            2: {"label": "Low",     "color": (144,238,144)},
            3: {"label": "Mild",    "color": (255,255,116)},
            4: {"label": "Severe",  "color": (215,25,28)}
        }

        # Panggil handler yang sama persis seperti saat worker selesai
        self.on_analysis_finished(fake)

    