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
from gui.new_shp_dialog import CreateShapefileDialog
from gui.worker import Worker
from gui.raster_processor import RasterHandler
from gui.vector_processor import VectorHandler
from gui.layer_manager import LayerManager
from app.disease_controller import DiseaseAnalysis
from app.water_controller import WaterAnalysis
from app.nutrient_controller import NutrientAnalysis
from app.result_model import AnalysisResult
from path_config import AppPaths
import os
import logging
import shutil

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(str(AppPaths.ui("main_window.ui")), self)
        self.setWindowTitle("mY App")
        self.setWindowIcon(QIcon(str(AppPaths.assets("defaults/textures/icon/edit-image.png"))))
        self._layer_id = 0
        self.elapsed_sec = 0
        self.active_thread = []
        self.queue_files = None
        self.time_str = str(0)
        self.current_crs = "Unknown"
        self.current_msg = "Processing..."
        self.layer_manager = LayerManager()
        self.viewer = Viewer(
            layer_manager=self.layer_manager, 
            parent=self.containerViewer
            )
        viewer_layout = QVBoxLayout(self.containerViewer)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.addWidget(self.viewer)
        # logger.info(f"Viewer panel tipe: {type(self.viewer)}, parent: {self.viewer.parent()}")

        self.layer_panel = LayerPanel(
            layer_manager=self.layer_manager,
            parent=self.containerLayer, 
            viewer=self.viewer
            )
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
        self.raster_handler = RasterHandler(layer_manager=self.layer_manager)
        self.vector_handler = VectorHandler(layer_manager=self.layer_manager)
        self.disease_ctrl = DiseaseAnalysis()
        self.water_ctrl = WaterAnalysis()
        self.nutrient_ctrl = NutrientAnalysis()
        self._setup_icons()
        self._setup_statusbar()
        self.statusBar().showMessage("Ready")
        self.statusBar().addPermanentWidget(self.progress_bar)
        self._connect_signals()
        self.viewer.mouseMoved.connect(self.update_coord_label)
        self.raster_handler.crsDetected.connect(self.update_crs_label)
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
        icon_tif = QIcon(str(AppPaths.assets("defaults/textures/icon/add_img.png")))
        icon_shp = QIcon(str(AppPaths.assets("defaults/textures/icon/poly.png")))
        icon_open = QIcon(str(AppPaths.assets("defaults/textures/icon/folder.png")))
        icon_exit = QIcon(str(AppPaths.assets("defaults/textures/icon/exit.png")))
        icon_model = QIcon(str(AppPaths.assets("defaults/textures/icon/deep-learning.png")))
        self.icon_disease = QIcon(str(AppPaths.assets("defaults/textures/icon/virus.png")))
        self.icon_mineral = QIcon(str(AppPaths.assets("defaults/textures/icon/nutrients.png")))
        self.icon_water = QIcon(str(AppPaths.assets("defaults/textures/icon/drop.png")))
        icon_hand = QIcon(str(AppPaths.assets("defaults/textures/icon/hand.png")))
        icon_zoom_in = QIcon(str(AppPaths.assets("defaults/textures/icon/zoom-in.png")))
        icon_zoom_out = QIcon(str(AppPaths.assets("defaults/textures/icon/zoom-out.png")))
        icon_fit_to_view = QIcon(str(AppPaths.assets("defaults/textures/icon/width.png")))
        icon_new_shp = QIcon(str(AppPaths.assets("defaults/textures/icon/edit_poly.png")))
        self.menuOpen.setIcon(icon_open)
        self.action_open_img.setIcon(icon_tif)
        self.action_open_shp.setIcon(icon_shp)
        self.action_add_raster_layer.setIcon(icon_tif)
        self.action_add_vector_layer.setIcon(icon_shp)
        self.action_new_shp_layer.setIcon(icon_new_shp)
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
        self.crs_label = QLabel("CRS: -")
        self.statusBar().addPermanentWidget(self.crs_label)
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

    def update_crs_label(self, crs):
        self.crs_label.setText(f"CRS: {crs}")
        self.current_crs = crs 

    def _status_bar_info(self, msg):
        self.statusBar().showMessage(f"{msg}", 3000)

    def start_worker(self, worker):
        self.active_thread.append(worker)
        self._setup_progress_dialog()
        worker.progress_signal.connect(
            self.handle_progress_dialog
        )
        worker.progress_signal.connect(
            self.update_progress_bar
        )
        worker.error_signal.connect(
            self.show_error_msg
        )
        self.pd.canceled.connect(
            worker.requestInterruption
        )
        worker.finished.connect(lambda: self.remove_worker(worker))
        worker.start()

    def remove_worker(self, worker):
        if worker in self.active_thread:
            self.active_thread.remove(worker)

    def _connect_signals(self):
        logger.info("Sinyal Action terhubung")
        self.raster_handler.crsDetected.connect(self.update_crs_label)
        self.raster_handler.originUpdated.connect(self.viewer.set_scene_origin)
        self.raster_handler.rasterUpdated.connect(self.viewer.render_geotiff)
        self.vector_handler.crsDetected.connect(self.update_crs_label)
        self.vector_handler.originUpdated.connect(self.viewer.set_scene_origin)
        self.layer_panel.layerUpdated.connect(self.viewer.update_list_ids)
        self.layer_panel.layerRemoveRequested.connect(self.remove_layer)
        self.layer_panel.layerSelected.connect(self.update_legend_from_layer)
        self.layer_panel.infoMsg.connect(self._status_bar_info)
        self.viewer.infoMsg.connect(self._status_bar_info)
        self.viewer.viewportChanged.connect(self.on_viewport_changed)
        self.viewer.drawFinished.connect(self.draw_shp_finished)
        self.action_open_shp.triggered.connect(self.open_vector_file)
        self.action_open_img.triggered.connect(self.open_img_file)
        self.action_add_raster_layer.triggered.connect(self.open_img_file)
        self.action_add_vector_layer.triggered.connect(self.open_vector_file)
        self.action_new_shp_layer.triggered.connect(self.create_new_shapefile)
        self.action_exit.triggered.connect(self.close)
        self.action_pan.toggled.connect(self.viewer.set_pan_mode)
        self.action_zoom_in.triggered.connect(self.viewer.zoom_in)
        self.action_zoom_out.triggered.connect(self.viewer.zoom_out)
        self.action_fit_to_view.triggered.connect(self.viewer.fit_to_view)
        self.action_disease_predict.triggered.connect(self.run_disease_prediction)
        self.action_water_predict.triggered.connect(self.run_water_prediction)
        self.action_nutrient_predict.triggered.connect(self.run_nutrient_prediction)
        # self.action_debug.triggered.connect(self.simulate_finished)

    def process_next_queue(self):
        if not self.queue_files:
            self.timer.stop()
            logger.info("Semua raster berhasil dimuat ke workspace!")
            return

        file = self.queue_files.pop(0)
        self.load_raster_layer(file)      

    def load_raster_layer(self, path):
        file_name = os.path.basename(path)
        self._layer_id += 1
        layer_id = self._layer_id
        raster_worker = Worker(
            self.raster_handler.add_raster,
            file_name,
            layer_id,
            path
        )
        raster_worker.finished_signal.connect(
            self.on_img_loaded
        )
        raster_worker.finished.connect(self.process_next_queue)
        self.start_worker(
            raster_worker
        )

    def load_vector_layer(self, path):
        file_name = os.path.basename(path)
        import fiona
        if path.lower().endswith(".gpkg"):
            gpkg_layers = fiona.listlayers(path)
            for lyr in gpkg_layers:
                if lyr != "app_layer_metadata":
                    self._layer_id += 1
                    layer_id = self._layer_id
                    layer = self.vector_handler.add_gpkg_layer(file_name, layer_id, path, lyr)
                    new_name = f"{file_name} | {lyr}"
                    self.layer_manager.add_layer(layer)
                    self.layer_panel.add_layer_item(layer.sid, new_name)
                    self.viewer._render_vector(layer.sid)
            return     
        elif path.lower().endswith((".shp")):
            self._layer_id += 1
            layer_id = self._layer_id
            layer = self.vector_handler.add_shapefile(file_name, layer_id, path)
            self.layer_manager.add_layer(layer)
            self.layer_panel.add_layer_item(layer.sid, layer.name)
            self.viewer._render_vector(layer.sid)

    def open_img_file(self):
        logger.info("Action: open_img ditekan")
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Supported Raster", "", "GeoTIFF (*.tif *.tiff);;Images (*.jpg *.png)"
        )
        if path:
            self.load_raster_layer(path)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.statusBar().showMessage("Ready")

    def open_vector_file(self):
        logger.info("Action: open_shp ditekan")
        path, _ = QFileDialog.getOpenFileName(self, "Open Supported Vector", "", "ESRI Shapefile (*.shp);;Geopackage (*.gpkg)")
        
        if path:
            self.load_vector_layer(path)
    
    def on_img_loaded(self, result):
        if result is None:
            logger.info("Gagal memuat raster: result None atau thread error")
        else:
            self.layer_manager.add_layer(result)
            self.layer_panel.add_layer_item(result.sid, result.name)
            self.viewer.render_geotiff(
                result.sid,
                init_view=True)

    def on_viewport_changed(self):
        canvas, zoom_ratio = self.viewer.get_viewport_state()
        self.raster_handler.set_viewport_state(
            canvas, 
            zoom_ratio
            )
        self.raster_handler.trigger_update_overview_level()

    def remove_layer(self, layer_id):
        layer = self.layer_manager.remove_layer(layer_id)
        if not layer:
            return
        self.delete_temp_folder(layer.name)
        self.viewer.remove_item(layer_id)
        self.layer_panel.remove_layer_item(layer_id)
        if layer.layer_type == "raster":
            self.raster_handler.remove_raster(layer_id)
        if layer.layer_type == "vector":
            self.vector_handler.remove_vector(layer_id)
        if self.layer_manager.is_empty:
            self.update_crs_label("Unknown")

    def delete_temp_folder(self, layer_name):
        name = layer_name.split(".")[0]
        try:
            if name:
                from path_config import AppPaths
                temp_dir = AppPaths.TEMP / name
                logger.info(f"Menghapus folder temp: {name}")
                if os.path.exists(temp_dir):
                    shutil.rmtree(str(temp_dir))
                    # logger.info(f"Folder temp dihapus: {temp_dir}")
        except Exception as e:
            logger.error(f"Gagal menghapus: {e}")
            
    def create_new_shapefile(self):
        logger.info("Action: action_new_shp_layer ditekan")
        dialog = CreateShapefileDialog(self, crs=self.current_crs)
        if dialog.exec_():
            path, dtype, crs = dialog.get_values()
            logger.info(f"Tipe geometri: {dtype}, CRS: {crs}")
            
            if path:
                self.viewer.temp_shp_path = path
                self.viewer.temp_shp_type = dtype
                self.viewer.temp_shp_crs = crs
                self.viewer.isDrawing = True
                self.viewer.setFocus(True)
                self.viewer.setCursor(Qt.CrossCursor)
                self.viewer.viewer.viewport().setCursor(Qt.CrossCursor)
                self.statusBar().showMessage("Draw polygon mode enabled. Left click to add points, right click to finish. Press enter/return to save, esc to cancel", 20000)
    
    def draw_shp_finished(self, conds, path):
        if conds:
            self.viewer.del_drawing()
            if path:
                self.load_vector_layer(path)

    def get_pathname_layers(self):
        logger.info("Update list layer combo box")
        layer_dict = {}
        if self.layer_panel.layer_ids:
            for lid in self.layer_panel.layer_ids:
                info = self.viewer.get_metadata(lid)
                name = info.get("Filename", None)
                path = info.get("Source", None)
                layer_dict.update({
                    lid: {
                        "Filename": name, 
                        "Source": path
                    }
                })
            # logger.info(f"Daftar layer: {layer_dict}")
        return layer_dict 

    def update_legend_from_layer(self, layer_id):
        logger.info("Legenda diperbarui!")
        layer = self.layer_manager.get_layer(layer_id)
        if not layer:
            return
        info = layer.metadata
        if not info:
            self.legend_panel.clear()
            return

        legend = None
        stats = None
        if info.get("Type") == "gpkg":
            legend, stats = self.vector_handler.read_gpkg_metadata(
                info["Source"],
                info["Layer_name"]
            )
        else:
            legend = info.get("Legend")
            stats = info.get("Stats")

        if not legend and not stats:
            self.legend_panel.clear()
            self.dockLegend.hide()
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
        # Inisiasi worker thread
        analysis_worker = Worker(controller.run, tif, shp, out)
        analysis_worker.finished_signal.connect(self.on_analysis_finished)
        self.start_worker(analysis_worker)
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
            self.queue_files = result.prediction_path
            if self.queue_files:
                try:
                    self.process_next_queue()
                except Exception as e:
                    self.show_error_msg(f"{str(e)}")
        else:
            try:
                self.load_vector_layer(result.prediction_path)
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
        self.time_str = str(0)

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
        self.time_str = str(0)
        self.statusBar().clearMessage()

    def run_disease_prediction(self):
        logger.info("action_disease_predict ditekan")
        metadata = self.get_pathname_layers()
        dialog = InputDialog(self, title="Disease Detection", icon=self.icon_disease, metadata=metadata)
        if dialog.exec_():
            tif, shp, out = dialog.get_values()
            self.run_analysis(self.disease_ctrl, tif, shp, out)

    def run_water_prediction(self):
        logger.info("action_water_predict ditekan")
        metadata = self.get_pathname_layers()
        dialog = InputDialog(self, title="Water Availability", icon=self.icon_water, metadata=metadata)
        if dialog.exec_():
            tif, shp, out = dialog.get_values()
            self.run_analysis(self.water_ctrl, tif, shp, out)

    def run_nutrient_prediction(self):
        logger.info("action_disease_predict ditekan")
        metadata = self.get_pathname_layers()
        dialog = InputDialog(self, title="Nutrient Availability", icon=self.icon_mineral, metadata=metadata)
        if dialog.exec_():
            tif, shp, out = dialog.get_values()
            self.run_analysis(self.nutrient_ctrl, tif, shp, out)

    def closeEvent(self, event):
        thread_running = False
        from path_config import AppPaths
        logger.info("Mencoba menutup aplikasi...")
        reply = QMessageBox.question(self, 'Exit', 'Are you sure?',
                                     QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            for worker in self.active_thread:
                if worker.isRunning():
                    thread_running = True
                    logger.info("Menghentikan worker thread sebelum keluar...")
                    worker.requestInterruption()
                    worker.quit()
                    worker.wait()
                    if hasattr(self, 'pd'):
                        self.pd.close()
            if thread_running:
                logger.info("Menunggu seluruh background thread selesai...")
            if AppPaths.TEMP.exists():
                logger.info("Menghapus cache di temporary folder...")
                import shutil
                shutil.rmtree(AppPaths.TEMP)
            logger.info("Cleanup selesai. Aplikasi ditutup")
            event.accept()
        else:
            logger.info("Batal menutup aplikasi.")
            event.ignore()

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

    