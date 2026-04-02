from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QLabel

from gui.viewer import Viewer
from gui.layer_panel import LayerPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/main_window.ui", self)

        self.viewer = Viewer(self.viewerPanel)
        self.layers = LayerPanel(self.layerPanel, self.viewer)

        self._setup_statusbar()

        self.viewer.mouseMoved.connect(self.update_coord_label)
        layer_id = self.viewer.add_raster("hasil_threshold.tif")
        self.layers.add_input_layer("Contoh TIF", layer_id)

    def _setup_statusbar(self):
        self.coord_label = QLabel("X: -, Y: -")
        self.statusBar().addPermanentWidget(self.coord_label)
        
    def update_coord_label(self, x, y):
        self.coord_label.setText(f"X: {x:.2f}, Y: {y:.2f}")


 