from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, 
    QGraphicsItemGroup
    )
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPolygonF, QPen, QColor
from PyQt5.QtCore import Qt, pyqtSignal, QPointF
import rasterio as rio
import geopandas as gpd
import numpy as np
import logging

logger = logging.getLogger(__name__)

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
        # self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.layout.addWidget(self.view)
        self.zoom = 0

    def add_raster(self, path):
        logger.info("Membuka raster")
        if path.lower().endswith((".png", ".jpg", ".jpeg")):
            pixmap = QPixmap(path)
        else:  # GeoTIFF Logic
            with rio.open(path) as src:
                # Baca data dan paksa ke float32 untuk perhitungan percentile
                dtype = src.dtypes[0]
                bands = src.read().astype(np.float32)
                count = src.count

                img_max = bands.max()
                
                # Normalisasi per band (Robust untuk uint16/float32)
                for i in range(count):
                    b = bands[i]
                    
                    if img_max > 0:
                        if img_max <= 5:
                            bands[i] = np.clip(b / img_max, 0, 1)
                        elif dtype == 'uint8':
                            bands[i] = np.clip(b / 255.0, 0, 1)
                        elif dtype == 'uint16':
                            bands[i] = np.clip(b / 65535.0, 0, 1)
                    else:
                        bands[i] = np.clip(b, 0, 1)

                # Penanganan Channel (RGB vs Grayscale)
                if count >= 3:
                    # Ambil 3 band pertama saja untuk visualisasi RGB
                    img_data = bands[:3]
                    img = (np.transpose(img_data, (1, 2, 0)) * 255).astype(np.uint8)
                    format_qimg = QImage.Format_RGB888
                    h, w, ch = img.shape
                else:
                    # Jika hanya 1 atau 2 band, tampilkan sebagai grayscale 
                    img = (bands[0] * 255).astype(np.uint8)
                    format_qimg = QImage.Format_Grayscale8
                    h, w = img.shape
                    ch = 1
                
                qimg = QImage(img.tobytes(), w, h, ch * w, format_qimg).copy() 
                pixmap = QPixmap.fromImage(qimg)

        # Tambahkan ke Scene
        item = self.scene.addPixmap(pixmap)
        item.setTransformationMode(Qt.FastTransformation)
        
        self._layer_id += 1
        layer_id = self._layer_id
        item.setZValue(layer_id)
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
        logger.info(f"Mengatur ulang z-order: {ordered_ids}")
        for z, lid in enumerate(ordered_ids):
            if lid in self.layer_items:
                self.layer_items[lid].setZValue(z)
        
        self.view.viewport().update()
        
    def add_shapefile(self, path):
        logger.info("Membuka shapefile")
        gdf = gpd.read_file(path)
        
        group = QGraphicsItemGroup()
        self.scene.addItem(group)

        for _, feature in gdf.iterrows():
            geom = feature.geometry
            if geom.geom_type == 'Polygon':
                self._draw_polygon_to_group(geom.exterior.coords, group)
            elif geom.geom_type == 'MultiPolygon':
                for poly in geom.geoms:
                    self._draw_polygon_to_group(poly.exterior.coords, group)

        self._layer_id += 1
        layer_id = self._layer_id

        group.setZValue(layer_id + 100)
        self.layer_items[layer_id] = group
        return layer_id

    def _draw_polygon_to_group(self, coords, group):
        # Konversi koordinat Geopandas ke QPolygonF milik Qt
        points = [QPointF(x, y) for x, y in coords]
        polygon_item = self.scene.addPolygon(QPolygonF(points))
        polygon_item.setPen(QPen(QColor(255, 0, 0, 128), 0.5))

        group.addToGroup(polygon_item)

