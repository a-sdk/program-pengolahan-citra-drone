from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QPixmap, QImage, QPainter
from PyQt5.QtCore import Qt, pyqtSignal

import rasterio as rio
import numpy as np

class Viewer(QWidget):
    mouseMoved = pyqtSignal(float, float)
    def __init__(self, parent = None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.layer_items = {}
        self._layer_id = 0
        self.setMouseTracking(True)
        self.view.setMouseTracking(True)
        self.view.setScene(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.layout.addWidget(self.view)
        self.zoom = 0

    def add_raster(self, path):
        if path.lower().endswith((".png", ".jpg", ".jpeg")):
            pixmap = QPixmap(path)

        else:  # geotiff
            with rio.open(path) as src:
                bands = src.read().astype(np.float32)
                count = src.count
                for i in range(count):
                    b = bands[i]
                    p2, p98 = np.percentile(b, (2, 98))
                    bands[i] = np.clip((b - p2) / (p98 - p2), 0, 1)

                img = (np.transpose(bands, (1, 2, 0)) * 255).astype(np.uint8)

                h, w, ch = img.shape
                qimg = QImage(img.data, w, h, ch*w, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg)

        item = self.scene.addPixmap(pixmap)
        item.setTransformationMode(Qt.SmoothTransformation)
        self._layer_id += 1
        layer_id = self._layer_id
        self.layer_items[layer_id] = item
        self.fit_to_view()

        return layer_id
    
    def set_visible(self, layer_id, visible):
        self.layer_items[layer_id].setVisible(visible)

    def remove_layer(self, layer_id):
        item = self.layer_items.pop(layer_id)
        self.scene.removeItem(item)

    def fit_to_view(self):
        rect = self.scene.itemsBoundingRect()
        self.view.fitInView(rect, Qt.KeepAspectRatio)
        self._zoom = 0

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            factor = 1.25
            self._zoom += 1
        else:
            factor = 0.8
            self._zoom -= 1

        self.view.scale(factor, factor)

    def mouseMoveEvent(self, event):
        pos = self.view.mapToScene(event.pos())
        x = pos.x()
        y = pos.y()
        self.mouseMoved.emit(x, y)

    def set_z_order(self, ordered_ids):
        for z, lid in enumerate(ordered_ids):
            self.layer_items[lid].setZValue(z)
        
