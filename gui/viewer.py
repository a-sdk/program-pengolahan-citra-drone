from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, 
    QGraphicsItemGroup, QGraphicsPixmapItem, QFrame,
    QGraphicsPathItem
)
from PyQt5.QtGui import (
    QPixmap, QImage, QPainter, 
    QPolygonF, QBrush, QPen, QColor,
    QTransform, QPainterPath
)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QEvent
import rasterio as rio
import geopandas as gpd
import numpy as np
import json
import logging

logger = logging.getLogger(__name__)

class Viewer(QWidget):
    mouseMoved = pyqtSignal(float, float)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.viewer = QGraphicsView()
        self.scene = QGraphicsScene()
        self.layer_items = {}
        self._layer_id = 0
        self.raster_info = {}
        self.vector_info = {}
        self.setMouseTracking(True)
        self.viewer.setMouseTracking(True)
        self.viewer.viewport().setMouseTracking(True)
        self.viewer.viewport().installEventFilter(self)
        self.viewer.setScene(self.scene)
        self.viewer.setRenderHint(QPainter.Antialiasing)
        self.viewer.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.viewer.setFrameShape(QFrame.NoFrame)
        self.viewer.setLineWidth(0)
        self.viewer.setStyleSheet("border: none;")
        self.main_layout.addWidget(self.viewer)
        self._zoom = 0

    def add_raster(self, path, isPrediction=False):
        logger.info("Membuka raster")
        if path.lower().endswith((".png", ".jpg", ".jpeg")):
            pixmap = QPixmap(path)
            isGeoTiff = False
        else:  # GeoTIFF Logic
            isGeoTiff = True
            with rio.open(path) as src:
                dtype = src.dtypes[0]
                bands = src.read().astype(np.float32)
                mask = src.read_masks(1)
                alpha = mask.astype(np.uint8)
                count = src.count
                crs = src.crs
                nodata = src.nodata
                tag = src.tags()
                h, w = src.shape
                t = src.transform
                pixel_width = abs(t.a)
                img_max = bands.max()
                img_min = bands.min()
                ch = 4
                qt_transform = QTransform(t.a, t.b, t.d, t.e, t.c, t.f)

                if img_max <= 4 and dtype == 'uint8':
                    isPrediction = True

                if isPrediction:
                    img = np.zeros((h, w, ch), dtype=np.uint8)
                    img_data = bands[0]
                    colors = {
                        0: [0, 0, 0, 0],
                        1: [0, 128, 0, 255],
                        2: [144, 238, 144, 255],
                        3: [255, 255, 116, 255],
                        4: [215, 25, 28, 255]
                    }
                    for val, color in colors.items():
                        img[img_data == val] = color
                # Jika bukan hasil prediksi
                else: 
                    # Normalisasi per band 
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
                        # Ambil 3 band pertama untuk visualisasi RGB
                        img_data = bands[:3]
                        rgb = (np.transpose(img_data, (1, 2, 0)) * 255).astype(np.uint8)
                        img = np.dstack((rgb, alpha))

                    else:
                        # Jika hanya 1 atau 2 band, tampilkan sebagai grayscale 
                        gray = (bands[0] * 255).astype(np.uint8)
                        alpha = np.full_like(gray, 255, dtype=np.uint8)
                        if mask is not None and np.any(mask):
                            alpha = mask.astype(np.uint8)
                        elif nodata is not None:
                            alpha[bands[0]==nodata] = 0
                        img = np.dstack((gray, gray, gray, alpha))
                
                qimg = QImage(img.tobytes(), w, h, ch * w, QImage.Format_RGBA8888).copy() 
                pixmap = QPixmap.fromImage(qimg)

        # Assign layer ID
        self._layer_id += 1
        layer_id = self._layer_id
        # Tambahkan ke Scene
        item = self.scene.addPixmap(pixmap)
        if isGeoTiff:
            item.setTransform(qt_transform)
            # Memeriksa legend dan stats jika citra hasil prediksi
            legend_dict = {}
            stats_dict = {}
            if isPrediction:
                if "LEGEND" in tag:
                    legend_dict = json.loads(tag.get("LEGEND", "{}"))
                if "STATS" in tag:
                    stats_dict = json.loads(tag.get("STATS", "{}"))

            # Simpan info raster
            self.raster_info[layer_id] = {
                "path": path,
                "legend": legend_dict,
                "stats": stats_dict,
                "dtype": str(dtype),
                "crs": crs.to_string() if crs else "Non-Georeferenced",
                "count": count,
                "nodata": nodata,
                "min_data": str(img_min),
                "max_data": str(img_max),
                "res": f"{pixel_width:.4f} m ({pixel_width*100:.1f} cm/px)"
            }
        self.layer_items[layer_id] = item
        item.setTransformationMode(Qt.FastTransformation)
        item.setAcceptHoverEvents(False)
        self.fit_to_view()
        return layer_id
    
    def _draw_polygon(self, coords, group, color):
        points = [QPointF(x, y) for x, y in coords]
        polygon_item = self.scene.addPolygon(QPolygonF(points))
        pen = QPen(QColor(0, 0, 0, 150))
        pen.setWidth(1)
        pen.setCosmetic(True)
        polygon_item.setPen(pen)
        polygon_item.setBrush(QColor(*color))
        group.addToGroup(polygon_item)

    def _add_vector(self, gdf, group, legend_dict=None, class_col=None):
        for _, feature in gdf.iterrows():
            geom = feature.geometry
            # Warna berdasarkan atribut
            color = (255, 0, 0, 50)
            if legend_dict and class_col:
                val = str(feature[class_col])
                if val in legend_dict:
                    color = legend_dict[val]["color"]
                    print(color)

            if geom is None or geom.is_empty:
                continue
            if geom.geom_type == 'Polygon':
                self._draw_polygon(geom.exterior.coords, group, color)
            elif geom.geom_type == 'MultiPolygon':
                for poly in geom.geoms:
                    self._draw_polygon(poly.exterior.coords, group, color)
            self.fit_to_view()

    def add_shapefile(self, path):
        logger.info("Membuka shapefile")
        self._layer_id += 1
        layer_id = self._layer_id
        gdf = gpd.read_file(path)
        group = QGraphicsItemGroup()
        self.scene.addItem(group)
        self.layer_items[layer_id] = group
        self.vector_info[layer_id] = {
            "type": "shp",
            "path": path,
            "crs": gdf.crs.to_string() if gdf.crs else "Unknown",
            "geom_type": str(gdf.geom_type.iloc[0]),
            "count": len(gdf)
        }

        self._add_vector(gdf, group)
        return layer_id
    
    def add_gpkg_layer(self, path, layer_name):
        logger.info(f"Membuka GPKG: {layer_name}")
        self._layer_id += 1
        layer_id = self._layer_id
        legend, stats = self.read_gpkg_metadata(path, layer_name)
        gdf = gpd.read_file(path, layer=layer_name)
        group = QGraphicsItemGroup()
        self.scene.addItem(group)
        self.layer_items[layer_id] = group
        self.vector_info[layer_id] = {
            "type": "gpkg",
            "path": path,
            "layer_name": layer_name,
            "crs": gdf.crs.to_string() if gdf.crs else "Unknown",
            "geom_type": str(gdf.geom_type.iloc[0]),
            "count": len(gdf),
            "legend": legend,
            "stats": stats
        }

        self._add_vector(
            gdf, 
            group,
            legend,
            "class"
        )
        return layer_id
    
    def set_visible(self, layer_id, visible):
        self.layer_items[layer_id].setVisible(visible)

    def remove_layer(self, layer_id):
        item = self.layer_items.pop(layer_id)
        self.scene.removeItem(item)

    def fit_to_view(self):
        rect = self.scene.itemsBoundingRect()
        self.viewer.fitInView(rect, Qt.KeepAspectRatio)
        self._zoom = 0

    def set_pan_mode(self, enabled: bool):
        if enabled:
            logger.info("action_pan: ON")
            self.viewer.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        else:
            logger.info("action_pan: OFF")
            self.viewer.setDragMode(QGraphicsView.DragMode.NoDrag)

    def zoom_in(self):
        self.viewer.scale(1.25, 1.25)

    def zoom_out(self):
        self.viewer.scale(0.8, 0.8)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            factor = 1.25
            self._zoom += 1
        else:
            factor = 0.8
            self._zoom -= 1

        self.viewer.scale(factor, factor)

    def eventFilter(self, source, event):
        if source is self.viewer.viewport() and event.type() == QEvent.Type.MouseMove:
            # Ambil posisi dan konversi ke scene
            scene_pos = self.viewer.mapToScene(event.pos())
            x = round(scene_pos.x(), 2)
            y = round(scene_pos.y(), 2)
            # print(f"Detected via Filter: {x}, {y}")
            self.mouseMoved.emit(x, y)
        return super().eventFilter(source, event)

    def set_z_order(self, ordered_ids):
        logger.info(f"Mengatur z-order: {ordered_ids}")
        for z, lid in enumerate(ordered_ids):
            if lid in self.layer_items:
                self.layer_items[lid].setZValue(z)
        self.viewer.viewport().update()       

    def get_metadata(self, layer_id):
        # Ambil item dari dictionary layer_items
        item = self.layer_items.get(layer_id)
        if not item: return None
        
        metadata = {
            "Layer ID": str(layer_id),
            "Z-Value": str(item.zValue()),
            "Visible": "Yes" if item.isVisible() else "No"
        }
        
        # Jika item adalah Raster (Pixmap)
        if isinstance(item, QGraphicsPixmapItem):
            info = self.raster_info.get(layer_id, {})
            metadata.update({
                        "Type": "Raster",
                        "Data Type (DType)": info.get("dtype", "Unknown"),
                        "CRS": info.get("crs", "Unknown"),
                        "NoData Value": info.get("nodata", "None"),
                        "Resolution": info.get("res", "Unknown")
                    })
        # Jika item adalah Shapefile
        elif isinstance(item, QGraphicsItemGroup):
            info = self.vector_info.get(layer_id, {})
            metadata.update({
                        "Type": "GeoPackage Layer" if info.get("type") == "gpkg" else "Shapefile",
                        "Layer Name": info.get("layer_name", "-"),
                        "Geometry": info.get("geom_type", "Polygon"),
                        "CRS": info.get("crs", "Unknown"),
                        "Feature Count": info.get("count", "0")
            })  
            
        return metadata

    def read_gpkg_metadata(self, path, layer_name):
        import sqlite3

        conn = sqlite3.connect(path)
        cur = conn.cursor()

        cur.execute("""
        SELECT legend_json, stats_json
        FROM app_layer_metadata
        WHERE layer_name = ?
        """, (layer_name,))

        row = cur.fetchone()
        conn.close()

        if row:
            return json.loads(row[0]), json.loads(row[1])

        return None, None