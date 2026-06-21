from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, 
    QGraphicsItemGroup, QGraphicsPixmapItem, QFrame,
    QGraphicsPolygonItem
)
from PyQt5.QtGui import (
    QPixmap, QPainter, QImage,
    QPolygonF, QPen, QColor,
    QPainterPath, QPixmapCache
)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QRectF, QEvent
from gui.layer_manager import Layer
import geopandas as gpd
import numpy as np
import json
import logging
 

logger = logging.getLogger(__name__)
class Viewer(QWidget):
    mouseMoved = pyqtSignal(float, float)
    infoMsg = pyqtSignal(str)
    drawFinished = pyqtSignal(bool, str)
    viewportChanged = pyqtSignal()
    infoCRS = pyqtSignal(str)
    def __init__(self, layer_manager, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.viewer = QGraphicsView()
        self.scene = QGraphicsScene()
        self.layer_manager = layer_manager
        self.layer_items = {}
        self.temp_shp_points = []
        self.temp_shp_type = None
        self.temp_shp_path = None
        self.temp_shp_crs = None
        self.active_poly_item = None
        self.commit_poly_item = []
        self.geo_coords = []
        self.list_poly = []
        self.isDrawing = False
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
        self.viewer.setFocusPolicy(Qt.StrongFocus)
        self.viewer.horizontalScrollBar().valueChanged.connect(self.viewportChanged.emit)
        self.viewer.verticalScrollBar().valueChanged.connect(self.viewportChanged.emit)
        self.main_layout.addWidget(self.viewer)
        self.scene_origin_x = None
        self.scene_origin_y = None
        self.base_view_scale = None
        self.base_raster_size = {}
        self.list_ids = []
        self._zoom = 0

    def set_scene_origin(self, x, y):
        self.scene_origin_x = x
        self.scene_origin_y = y
        logger.info(
            f"SET origin: x={round(x, 2)}, y={round(y,2)}"
        )

    def update_list_ids(self, ids):
        self.list_ids = ids

    def get_viewport_state(self):
        logger.info(
            f"EMIT viewport state: "
            f"base={self.base_view_scale} "
        )
        scale = self.viewer.transform().m11()
        canvas = self.viewer.mapToScene(self.viewer.viewport().rect()).boundingRect()
        if self.base_view_scale is None:
            self.base_view_scale = scale 
        if self.base_view_scale == 1:
            self.base_view_scale *= scale
        zoom_ratio = scale / self.base_view_scale
        logger.info(
            f"scale={round(scale, 2)}, "
            f"base={round(self.base_view_scale, 2)}, "
            f"ratio={round(zoom_ratio, 2)}"
        ) 
        return canvas, zoom_ratio
    
    def render_geotiff(self, layer_id, init_view=False):
        layer = self.layer_manager.get_layer(layer_id)
        info = layer.metadata
        img = layer.item
        transform = layer.qtransform
        w = info["width"]
        h = info["height"]
        # Map top left 0, 0
        top_left = transform.map(QPointF(0, 0))
        bot_right = transform.map(QPointF(w, h))
        from PyQt5 import sip
        ptr = sip.voidptr(img.ctypes.data)
        qimg = QImage(ptr, img.shape[1], img.shape[0], img.strides[0], QImage.Format_RGBA8888)
        logger.info(f"Membuat QImage: w={qimg.width()}, h={qimg.height()}")
        # logger.info(f"qimg.inbytes={qimg.sizeInBytes()/1024**2:.1f} MB")
        # logger.info(f"RAM: {process.memory_info().rss / 1024**2:.1f} MB")
        pixmap = QPixmap.fromImage(qimg)
        logger.info(f"Membuat QPixmap: w={pixmap.width()}, h={pixmap.height()}")
        # logger.info(f"RAM sebelum del: {process.memory_info().rss / 1024**2:.1f} MB")
        del img
        del qimg
        import gc
        gc.collect()
        # logger.info(f"RAM setelah del: {process.memory_info().rss / 1024**2:.1f} MB")
        if layer_id in self.layer_items and self.layer_items[layer_id] != None:
            logger.info(f"Layer {layer_id} sudah ada!")
            item = self.layer_items[layer_id]
            item.setPixmap(pixmap)
            logger.info(f"Memperbarui pixmap di scene...")
        else:
            logger.info(f"Layer {layer_id} belum ada!")
            self.base_raster_size[layer_id] = (w, h)
            # Set bounding scene
            if len(self.base_raster_size) == 1:
                logger.info("Mengatur sceneRect")
                self.scene.setSceneRect(
                    top_left.x(),
                    top_left.y(),
                    bot_right.x() - top_left.x(),
                    bot_right.y() - top_left.y()
                )
                logger.info(f"SceneRect sesuai origin: {self.scene.sceneRect()}")
            item = self.scene.addPixmap(pixmap)
            logger.info(f"Menambah pixmap ke scene...")
            self.layer_items[layer_id] = item

        # logger.info(f"{self.layer_items}")
        item.setTransform(transform)
        item.setTransformationMode(Qt.FastTransformation)
        item.setAcceptHoverEvents(False)
        self.set_z_order(self.list_ids)

        if init_view and h > 10000 and w > 10000:
            self.fit_to_view()

    def _draw_poly_feature(self, coords, group, color):
        points = [
            QPointF(
                x - self.scene_origin_x, 
                y - self.scene_origin_y
            ) 
            for x, y in coords
        ]
        polygon_item = self.scene.addPolygon(QPolygonF(points))
        pen = QPen(QColor(0, 0, 0, 150))
        pen.setWidth(1)
        pen.setCosmetic(True)
        polygon_item.setPen(pen)
        polygon_item.setBrush(QColor(*color))
        group.addToGroup(polygon_item)

    def _draw_line_feature(self, coords, group, color):
        path = QPainterPath()
        points = [
            QPointF(
                x - self.scene_origin_x,
                y - self.scene_origin_y
            ) 
            for x, y in coords
        ]
        if points:
            path.moveTo(points[0])
            for pt in points[1:]:
                path.lineTo(pt)
        
        line_item = self.scene.addPath(path)
        pen = QPen(QColor(*color))
        pen.setWidth(5)
        pen.setCosmetic(True)
        line_item.setPen(pen)
        group.addToGroup(line_item)

    def _draw_point_feature(self, x, y, group, color):
        r = 0.2
        sx = x - self.scene_origin_x
        sy = y - self.scene_origin_y
        point_item = self.scene.addEllipse(sx-r, sy-r, r*2, r*2)
        point_item.setPen(QPen(Qt.black, 0))
        point_item.setBrush(QColor(*color))
        group.addToGroup(point_item)

    def _add_vector(self, gdf, group, legend_dict=None, class_col=None):
        self.infoCRS.emit(gdf.crs.to_string() if gdf.crs else "Unknown")
        bounds = gdf.total_bounds
        xmin, ymin, xmax, ymax = bounds
        if self.scene_origin_x is None:
            self.set_origin(xmin, ymax)
        for _, feature in gdf.iterrows():
            geom = feature.geometry
            color = (255, 255, 116, 80)
            if legend_dict and class_col:
                val = str(feature[class_col])
                if float(val) < 1: # Cek jika hasil prediksi berupa regresi (0-1)
                    for key, data in legend_dict.items():
                        low, high = data["range"]
                        if low <= float(val) < high:
                            color = data["color"] # Warna berdasarkan rentang nilai
                            # logger.info(f"Value: {val} | Label: {data['label']} | Color: {color}")
                            break
                elif val in legend_dict:
                    color = legend_dict[val]["color"]
                    label = legend_dict[val]["label"]
                    # logger.info(f"Value: {val} | Label: {label} | Color: {color}")

            if geom is None or geom.is_empty:
                continue
            if geom.geom_type == "Polygon":
                self._draw_poly_feature(geom.exterior.coords, group, color)
            elif geom.geom_type == "MultiPolygon":
                for poly in geom.geoms:
                    self._draw_poly_feature(poly.exterior.coords, group, color)
            elif geom.geom_type == "LineString":
                self._draw_line_feature(geom.coords, group, color)
            elif geom.geom_type == "Point":
                self._draw_point_feature(geom.x, geom.y, group, color)
        self.set_z_order(self.list_ids)
            
    def add_shapefile(self, name, layer_id, path):
        logger.info(F"==== TAMBAH VEKTOR {name} DI LAYER: {layer_id} ====")
        logger.info("Membuka shapefile")
        gdf = gpd.read_file(path)
        group = QGraphicsItemGroup()
        self.scene.addItem(group)
        self.layer_items[layer_id] = group
        # logger.info(f"{self.layer_items}")
        info = {
            "Name": name,
            "Source": path,
            "Type": "shp",
            "CRS": gdf.crs.to_string() if gdf.crs else "Unknown",
            "Geom_type": str(gdf.geom_type.iloc[0]),
            "Count": len(gdf)
        }
        self.vector_info[layer_id] = info
        self._add_vector(gdf, group)
        layer = Layer(
            sid=layer_id,
            name=name,
            item=gdf,
            metadata=info,
            crs=info["CRS"],
            qtransform=None
        )
        return layer
        
    def add_gpkg_layer(self, name, layer_id, path, layer_name):
        logger.info(F"==== TAMBAH VEKTOR {layer_name} DI LAYER: {layer_id} ====")
        logger.info("Membuka GPKG...")
        gdf = gpd.read_file(path, layer=layer_name)
        legend, stats = self.read_gpkg_metadata(path, layer_name)
        group = QGraphicsItemGroup()
        self.scene.addItem(group)
        self.layer_items[layer_id] = group
        # logger.info(f"{self.layer_items}")
        info = {
            "Name": name, 
            "Source": path,
            "Type": "gpkg",
            "Layer_name": layer_name,
            "CRS": gdf.crs.to_string() if gdf.crs else "Unknown",
            "Geom_type": str(gdf.geom_type.iloc[0]),
            "Count": len(gdf),
            "Legend": legend,
            "Stats": stats
        }
        self.vector_info[layer_id] = info
        self._add_vector(
            gdf, 
            group,
            legend,
            "preds"
        )

        layer = Layer(
            sid=layer_id,
            name=layer_name,
            item=gdf,
            metadata=info,
            crs=info["CRS"],
            qtransform=None
        )
        return layer
        
    def set_visible(self, layer_id, visible):
        self.layer_items[layer_id].setVisible(visible)

    def remove_item(self, layer_id):
        item = self.layer_items.pop(layer_id, None)
        self.vector_info.pop(layer_id, None)
        self.base_raster_size.pop(layer_id, None)
        if item:
            self.scene.removeItem(item)
            if hasattr(item, 'deleteLater'):
                item.deleteLater()
            if hasattr(item, 'setPixmap'):
                item.setPixmap(QPixmap())
            item = None
        # logger.info(f"layer_items  : {list(self.layer_items.keys())}")
        if not self.layer_items:
            self.scene_origin_x = None
            self.scene_origin_y = None
            self.scene.clear()
        # Clear viewer and scene
        self.viewer.viewport().update()
        self.scene.update()
        QPixmapCache.clear()

    def apply_view_transform(self):
        t = self.viewer.transform()
        if t.m22() > 0:
            self.viewer.scale(1, -1)

    def fit_to_view(self):
        logger.info("Fit to view diklik.")
        combined_rect = QRectF()
        all_items = self.scene.items()
        has_visible_item = False
        for item in all_items:
            if item.isVisible() and hasattr(item, 'pixmap'):
                if not has_visible_item:
                    combined_rect = item.sceneBoundingRect()
                    has_visible_item = True
                else:
                    combined_rect = combined_rect.united(item.sceneBoundingRect())
        if has_visible_item and not combined_rect.isEmpty():
            self.viewer.fitInView(combined_rect, Qt.KeepAspectRatio)
        else:
            rect = self.scene.itemsBoundingRect()
            self.viewer.fitInView(rect, Qt.KeepAspectRatio)
        self.apply_view_transform()

    def set_pan_mode(self, enabled: bool):
        if enabled:
            logger.info("action_pan: ON")
            self.viewer.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        else:
            logger.info("action_pan: OFF")
            self.viewer.setDragMode(QGraphicsView.DragMode.NoDrag)

    def zoom_in(self):
        self._zoom += 1
        self.viewer.scale(1.05, 1.05)
        self.viewportChanged.emit()

    def zoom_out(self):
        self._zoom -= 1
        self.viewer.scale(0.8, 0.8)
        self.viewportChanged.emit()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.viewportChanged.emit()
    
    def eventFilter(self, source, event):
        if source is self.viewer.viewport() and event.type() == QEvent.Type.MouseMove:
            # Ambil posisi dan konversi ke scene
            scene_pos = self.viewer.mapToScene(event.pos())
            if self.scene_origin_x is not None and self.scene_origin_y is not None:
                world_x = round(scene_pos.x() + self.scene_origin_x, 2)
                world_y = round(scene_pos.y() + self.scene_origin_y, 2)
            else:
                world_x = round(scene_pos.x(), 2)
                world_y = round(scene_pos.y(), 2)
            self.mouseMoved.emit(world_x, world_y)
        return super().eventFilter(source, event)
    
    def update_draw_polygon(self):
        if not self.temp_shp_points:
            return
        
        if self.active_poly_item:
            self.scene.removeItem(self.active_poly_item)

        polygon_data = QPolygonF(self.temp_shp_points)
        self.active_poly_item = QGraphicsPolygonItem(polygon_data)
        pen = QPen(QColor(255, 0, 0, 150))
        pen.setWidth(1)
        pen.setCosmetic(True)
        self.active_poly_item.setPen(pen)
        self.active_poly_item.setBrush(QColor(255, 0, 0, 50))
        self.scene.addItem(self.active_poly_item)

    def mousePressEvent(self, event): 
        if self.isDrawing and event.button() == Qt.MouseButton.LeftButton:
            # logger.info("Mode gambar: klik kiri")
            # Tambah titik sudut
            pixel_pos = event.pos()
            scene_pos = self.viewer.mapToScene(pixel_pos)
            self.temp_shp_points.append(scene_pos)
            if self.scene_origin_x is not None and self.scene_origin_y is not None:
                world_x = scene_pos.x() + self.scene_origin_x
                world_y = scene_pos.y() + self.scene_origin_y
            coords = (world_x, world_y)
            self.geo_coords.append(coords)
            if self.temp_shp_type == "Point":
                self.finalize_polygon()
            else:
                self.update_draw_polygon()
            
        elif self.isDrawing and event.button() == Qt.MouseButton.RightButton:
            # logger.info("Mode gambar: klik kanan")
            num_points = len(self.temp_shp_points)
            if self.temp_shp_type == "Polygon" and num_points < 3:
                self.infoMsg.emit("Polygon require 3 or more points!")
            elif self.temp_shp_type == "LineString" and num_points < 2:
                self.infoMsg.emit("Line require 2 or more points!")
            elif self.temp_shp_type == "Point" and num_points < 1:
                self.infoMsg.emit("Point not defined!")
            else:
                self.finalize_polygon()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            logger.info("Mode gambar: selesai")
            self.save_polygon()
            if self.isDrawing:
                self.del_drawing()
        if event.key() == Qt.Key_Escape:
            logger.info("Mode gambar: keluar")
            if self.isDrawing:
                self.del_drawing()

    def del_drawing(self):
        self.viewer.setCursor(Qt.ArrowCursor)
        self.viewer.viewport().setCursor(Qt.ArrowCursor)
        self.infoMsg.emit("Draw polygon mode disabled")
        self.viewer.setFocus(False)
        self.isDrawing = False
        if self.active_poly_item:
            self.scene.removeItem(self.active_poly_item)
            self.active_poly_item = None
        if self.commit_poly_item:
            for item in self.commit_poly_item:
                self.scene.removeItem(item)
        self.temp_shp_points.clear()
        self.geo_coords.clear()
        self.list_poly.clear()
        self.commit_poly_item.clear()
        self.viewer.viewport().update()

    def set_z_order(self, ordered_ids):
        for i, lid in enumerate(ordered_ids):
            if lid in self.layer_items:
                z = len(ordered_ids) - i
                self.layer_items[lid].setZValue(z)
                logger.info(
                    f"Mengatur z-order: "
                    f"id={lid} -> z-order={z}"
                    )
        self.viewer.viewport().update()       

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
    
    def finalize_polygon(self):
        from shapely.geometry import Point, LineString, Polygon
        GEOM_MAPPING = {
            "Point": Point,
            "LineString": LineString,
            "Polygon": Polygon
        }
        dtype = GEOM_MAPPING.get(self.temp_shp_type)
        if not dtype:
            return
        try:
            if dtype == "Point":
                geom = dtype(self.geo_coords[0])
            else:
                geom = dtype(self.geo_coords)
                self.list_poly.append(geom)
                # logger.info(f"Polygon yang dibuat: {self.list_poly}")
            if not geom.is_valid:
                self.infoMsg.emit("Geometry is not valid")
                logger.info("Geometri tidak valid")
                return
            final_poly_item = QGraphicsPolygonItem(QPolygonF(self.temp_shp_points))
            pen = QPen(QColor(153, 245, 39, 150))
            pen.setWidth(1)
            pen.setCosmetic(True)
            final_poly_item.setPen(pen)
            final_poly_item.setBrush(QColor(153, 245, 39, 50))
            self.commit_poly_item.append(final_poly_item)
            self.scene.addItem(final_poly_item)

            if self.active_poly_item:
                self.scene.removeItem(self.active_poly_item)
                self.active_poly_item = None
                self.geo_coords.clear()
                self.temp_shp_points.clear()
                
        except Exception as e:
            logger.error(f"ERROR: {type(e).__name__}: {e}", exc_info=True)

    def save_polygon(self):
        try:
            gdf = gpd.GeoDataFrame({'id':range(len(self.list_poly))}, crs=self.temp_shp_crs, geometry=self.list_poly)
            gdf.to_file(self.temp_shp_path, driver="ESRI Shapefile")
            self.drawFinished.emit(True, self.temp_shp_path)

        except Exception as e:
            logger.error(f"ERROR: {type(e).__name__}: {e}", exc_info=True)