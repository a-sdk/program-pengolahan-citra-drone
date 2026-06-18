from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, 
    QGraphicsItemGroup, QGraphicsPixmapItem, QFrame,
    QGraphicsPolygonItem
)
from PyQt5.QtGui import (
    QPixmap, QImage, QPainter, 
    QPolygonF, QBrush, QPen, QColor,
    QTransform, QPainterPath, QPixmapCache, QMouseEvent
)
from gui.worker import WorkerHelper
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QEvent, QTimer
from path_config import AppPaths
import geopandas as gpd
import numpy as np
import json
import os
import logging
import psutil 

logger = logging.getLogger(__name__)
process = psutil.Process(os.getpid())

class Viewer(QWidget):
    mouseMoved = pyqtSignal(float, float)
    infoCRS = pyqtSignal(str)
    infoMsg = pyqtSignal(str)
    drawFinished = pyqtSignal(bool, str)
    OVERVIEW_FACTORS = [2,4,8,16,32]
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.viewer = QGraphicsView()
        self.scene = QGraphicsScene()
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
        self.viewer.setFocusPolicy(Qt.StrongFocus)
        self.viewer.horizontalScrollBar().valueChanged.connect(self.trigger_update_overview_level)
        self.viewer.verticalScrollBar().valueChanged.connect(self.trigger_update_overview_level)
        self.main_layout.addWidget(self.viewer)
        self.scene_origin_x = None
        self.scene_origin_y = None
        self._zoom = 0
        self._factor = 0
        self._middle_pan = False
        self.base_view_scale = None
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.update_overview_level)
        self.debounce_delay = 350 #ms
        
    def choose_display_factor(self, width):
        if width >= 10000:
            factor = 32
        elif width > 8000:
            factor = 16
        elif width > 5000:
            factor = 8
        else:
            factor = 4
        return factor

    def ensure_scene_origin(self, xmin, ymax):
        if self.scene_origin_x is None:
            self.scene_origin_x = xmin
            self.scene_origin_y = ymax

    def update_transform(self, transform, w, h, out_w, out_h):
        from rasterio.transform import Affine
        t1 = transform * Affine.scale(
            w / out_w,
            h / out_h   
        ) 
        final_transform = QTransform(
            t1.a, t1.b, 
            t1.d, t1.e, 
            t1.c - self.scene_origin_x, t1.f - self.scene_origin_y
        )
        return final_transform

    def read_overview(self, src, factor): 
        h, w = src.shape
        out_h = max(1, h // factor)
        out_w = max(1, w // factor)
        if src.count >= 3:
            data = src.read(
                [1, 2, 3],
                out_shape=(3, out_h, out_w)
            )
            # logger.info(f"RAM: {process.memory_info().rss / 1024**2:.1f} MB")
        else:
            data = src.read(
                out_shape=(src.count, out_h, out_w)
            )
            # logger.info(f"RAM: {process.memory_info().rss / 1024**2:.1f} MB")
        
        mask = src.read_masks(
            1, 
            out_shape=(out_h, out_w)
        )

        return data, mask

    def prepare_raster(self, bands, mask, dtype, count, nodata, isPrediction):
        alpha = mask.astype(np.uint8)
        # logger.info(f"bands.nbytes={bands.nbytes/1024**2:.1f} MB")
        # logger.info(f"alpha.nbytes={alpha.nbytes/1024**2:.1f} MB")
        if isPrediction:
            h, w = bands.shape[1:]
            img = np.zeros((h, w, 4), dtype=np.uint8)
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
            # Penanganan Channel (RGB vs Grayscale)
            if count >= 3 and dtype == 'uint16':
                # Ambil 3 band pertama untuk visualisasi RGB
                # logger.info("Melakukan transpose...")
                img_data = bands[:3]
                rgb = np.transpose((img_data >> 8), (1, 2, 0)).astype(np.uint8) 
                # logger.info(f"rgb.nbytes={rgb.nbytes/1024**2:.1f} MB")
                # logger.info(f"rgb:{rgb.flags['C_CONTIGUOUS']}")
                # logger.info(f"rgb:{rgb.flags['OWNDATA']}")
                img = np.dstack((rgb, alpha))
                del bands
                del rgb
                # logger.info(f"RAM: {process.memory_info().rss / 1024**2:.1f} MB")

            else:
                # Jika hanya 1 atau 2 band, tampilkan sebagai grayscale 
                gray = (bands[0] * 255).astype(np.uint8)
                # logger.info(f"gray.nbytes={gray.nbytes/1024**2:.1f} MB")
                if nodata is not None:
                    alpha = np.where(bands[0] == nodata, 0, alpha).astype(np.uint8)
                img = np.dstack((gray, gray, gray, alpha))
                del bands
                del gray
        # logger.info(f"img.nbytes={img.nbytes/1024**2:.1f} MB")
        img = np.ascontiguousarray(img)
        return img
    
    def display_raster(self, layer_id, img, qt_transform, init_view=False):
        info = self.raster_info[layer_id]
        h = info["height"]
        w = info["width"]
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
        # Tambahkan ke Scene
        # Cek jika sudah ada
        if layer_id in self.layer_items and self.layer_items[layer_id] != None:
            logger.info(f"Layer {layer_id} sudah ada!")
            item = self.layer_items[layer_id]
            item.setPixmap(pixmap)
            logger.info(f"Memperbarui pixmap di scene...")
        else:
            logger.info(f"Layer {layer_id} belum ada!")
            item = self.scene.addPixmap(pixmap)
            logger.info(f"Menambah pixmap ke scene...")
            self.layer_items[layer_id] = item

        # logger.info(f"{self.layer_items}")
        item.setTransform(qt_transform)
        item.setTransformationMode(Qt.FastTransformation)
        item.setAcceptHoverEvents(False)
        if init_view and h > 10000 and w > 10000:
            self.fit_to_view()

    def add_raster(self, name, layer_id, path, hooks=None):
        import rasterio as rio
        helper = WorkerHelper(hooks)
        filename = name.split(".")[0]
        temp_dir = AppPaths.TEMP / filename
        temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"RAM: {process.memory_info().rss / 1024**2:.1f} MB")
        logger.info(F"==== TAMBAH RASTER {name} DI LAYER: {layer_id} ====")
        logger.info("Membuka raster...")
        helper.progress(20, "Loading raster...")
        if helper.cancelled(): return None
        if path.lower().endswith((".png", ".jpg", ".jpeg")):
            isGeoTiff = False
            return path
        
        else:  # GeoTIFF Logic
            isGeoTiff = True
            logger.info("Membaca metadata raster...")
            helper.progress(45, "Fetching raster metadata...")
            if helper.cancelled(): return None
            with rio.open(path) as src:
                # Metadata raster
                dtype = src.dtypes[0]
                count = src.count
                crs = src.crs
                nodata = src.nodata
                tag = src.tags()
                h, w = src.shape
                t = src.transform
                # has_overview = len(src.overviews(1)) > 0
                self.ensure_scene_origin(t.c, t.f)
                pixel_width = abs(t.a) 
                display_factor = self.choose_display_factor(w)
                self._factor = display_factor
                logger.info(f"Display factor: {display_factor}")
                if display_factor < 16:
                    self.OVERVIEW_FACTORS.insert(0, 1)
                helper.progress(55, "Generating overview...")
                # Buat overview 
                current_build = 1
                for build_factor in self.OVERVIEW_FACTORS:
                    if helper.cancelled(): return None
                    total_build = len(self.OVERVIEW_FACTORS)
                    rel_progress = 60 + int((current_build/total_build) * 25)
                    helper.progress(rel_progress, f"Generating overview {current_build}/{total_build}")
                    preview, mask = self.read_overview(src, build_factor)
                    np.savez_compressed(
                        str(temp_dir/f"f{build_factor}.npz"),
                        bands=preview,
                        mask=mask
                    )
                    build_factor *= 2
                    current_build += 1
                # Load overview yang dibuat
                helper.progress(85, "Loading overview...")
                if helper.cancelled(): return None
                arr = np.load(str(temp_dir/f"f{display_factor}.npz"))
                bands = arr["bands"]
                mask = arr["mask"]
                # Transform overview
                out_h = bands.shape[1]
                out_w = bands.shape[2]
                qt_transform = self.update_transform(
                    t, w, h, out_w, out_h
                )

            # Cek jenis citra
            if "PREDICTION" in tag and dtype == 'uint8':
                isPrediction = True
            else:
                isPrediction = False
            
            img = self.prepare_raster(bands, mask, dtype, count, nodata, isPrediction)
            
 
        if isGeoTiff:
                # Memeriksa legend dan stats jika citra hasil prediksi
                legend_dict = {}
                stats_dict = {}
                if isPrediction:
                    if "LEGEND" in tag:
                        legend_dict = json.loads(tag.get("LEGEND", "{}"))
                    if "STATS" in tag:
                        stats_dict = json.loads(tag.get("STATS", "{}"))
                helper.progress(95, "Saving raster metadata...")
                if helper.cancelled(): return None
                # Simpan info raster
                self.raster_info[layer_id] = {
                    "name": name,
                    "path": path,
                    "legend": legend_dict,
                    "stats": stats_dict,
                    "dtype": str(dtype),
                    "crs": crs.to_string() if crs else "Non-Georeferenced",
                    "count": count,
                    "nodata": nodata,
                    "transform": t,
                    "height": h,
                    "width": w,
                    "res": f"{pixel_width:.4f} m ({pixel_width*100:.1f} cm/px)",
                    "current_factor": display_factor,
                    "base_factor": display_factor,
                    "cache_dir": str(temp_dir),
                    "is_prediction": isPrediction
                }
        self.infoCRS.emit(crs.to_string() if crs else "Unknown")
        helper.progress(100, "Done")
        return {
            "name": name,
            "layer_id": layer_id,
            "img": img,
            "img_transform": qt_transform
        }
    
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
        self.ensure_scene_origin(xmin, ymax)
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
                            logger.info(f"Value: {val} | Label: {data['label']} | Color: {color}")
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
            
    def add_shapefile(self, name, layer_id, path):
        logger.info("Membuka shapefile")
        gdf = gpd.read_file(path)
        group = QGraphicsItemGroup()
        self.scene.addItem(group)
        self.layer_items[layer_id] = group
        # logger.info(f"{self.layer_items}")
        self.vector_info[layer_id] = {
            "name": name,
            "type": "shp",
            "path": path,
            "crs": gdf.crs.to_string() if gdf.crs else "Unknown",
            "geom_type": str(gdf.geom_type.iloc[0]),
            "count": len(gdf)
        }

        self._add_vector(gdf, group)
        
    def add_gpkg_layer(self, name, layer_id, path, layer_name):
        logger.info(f"Membuka GPKG: {layer_name}")
        gdf = gpd.read_file(path, layer=layer_name)
        legend, stats = self.read_gpkg_metadata(path, layer_name)
        group = QGraphicsItemGroup()
        self.scene.addItem(group)
        self.layer_items[layer_id] = group
        # logger.info(f"{self.layer_items}")
        self.vector_info[layer_id] = {
            "type": "gpkg",
            "path": path,
            "name": name, 
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
            "preds"
        )
        
    def set_visible(self, layer_id, visible):
        self.layer_items[layer_id].setVisible(visible)

    def remove_layer(self, layer_id):
        item = self.layer_items.pop(layer_id)
        self.raster_info.pop(layer_id, None)
        self.vector_info.pop(layer_id, None)
        if item:
            self.scene.removeItem(item)
            if hasattr(item, 'deleteLater'):
                item.deleteLater()
            if hasattr(item, 'setPixmap'):
                item.setPixmap(QPixmap())
            item = None
        # logger.info(f"layer_items  : {list(self.layer_items.keys())}")
        if not self.layer_items:
            self.base_view_scale = None
            self.scene_origin_x = None
            self.scene_origin_y = None
            self.infoCRS.emit("Unknown")
            self.scene.clear()
        # Clear viewer and scene
        self.viewer.viewport().update()
        self.scene.update()
        QPixmapCache.clear()

    def apply_view_transform(self):
        t = self.viewer.transform()
        if t.m22() > 0:
            self.viewer.scale(1, -1)

    def choose_factor(self, base_factor, ratio):
        import math
        if ratio >=1:
            zoom_steps = math.ceil(math.log2(ratio))
        else:
            zoom_steps = -math.ceil(math.log2(1/ratio))   
        steps = {
            1: 0,
            2: 1,
            4: 2,
            8: 3,
            16: 4,
            32: 5
        }
        level = steps[base_factor] - zoom_steps
        level = max(0, min(5, level))
        return [1, 2, 4, 8, 16, 32][level]
        
    def reload_overview(self, layer_id, factor):
        from pathlib import Path
        info = self.raster_info[layer_id]
        raster_height = info["height"]
        raster_width = info["width"]
        
        if factor == 1 and raster_width > 10000 and raster_height > 10000:
            self.update_viewport_raster(layer_id)
            logger.info(f"Reload layer {layer_id} -> f{factor} -> window_reading")
        elif factor != info["current_factor"]:
            cache_dir = Path(info["cache_dir"])
            arr = np.load(str(cache_dir/f"f{factor}.npz"))
            bands = arr["bands"]
            mask = arr["mask"]

            img = self.prepare_raster(
                bands,
                mask,
                info["dtype"],
                info["count"],
                info["nodata"],
                info["is_prediction"]
            )
            
            pixmap_transform = self.update_transform(
                info["transform"], 
                info["width"], 
                info["height"], 
                bands.shape[2],
                bands.shape[1]
            )

            self.display_raster(layer_id, img, pixmap_transform, init_view=False)
            logger.info(f"Reload layer {layer_id} -> f{factor} {bands.shape}")
        info["current_factor"] = factor     
        # logger.info(f"scene bounding = {self.scene.itemsBoundingRect()}")
        # logger.info(f"item rect = {item.boundingRect()}, scene rect = {self.scene.sceneRect()}")
        # logger.info(f"VScroll max = {self.viewer.verticalScrollBar().maximum()}")
        # logger.info(f"HScroll max = {self.viewer.horizontalScrollBar().maximum()}")

    def update_overview_level(self):
        logger.info("UPDATE OVERVIEW LEVEL!")
        logger.info(
            f"ENTER update_overview_level: "
            f"base={self.base_view_scale}"
        )
        if not self.layer_items:
            return
        
        scale = self.viewer.transform().m11()
        if self.base_view_scale is None:
            self.base_view_scale = scale 
        if self.base_view_scale == 1:
            self.base_view_scale *= scale
        zoom_ratio = scale / self.base_view_scale
        for layer_id, info in self.raster_info.items():
            logger.info(f"==== INFO LAYER {layer_id} ====")
            base_factor = info["base_factor"]
            current_factor = self.choose_factor(base_factor, zoom_ratio)
            logger.info(
                f"layer={layer_id}, scale={scale:.4f},"
                f"base={self.base_view_scale:.4f}, factor={current_factor}"
                )
            self.reload_overview(layer_id, current_factor)
            
    
    def trigger_update_overview_level(self):
        self.debounce_timer.stop() # Stop timer
        self.debounce_timer.start(self.debounce_delay) # Mulai ulang

    def fit_to_view(self):
        rect = self.scene.itemsBoundingRect()
        self.viewer.fitInView(rect, Qt.KeepAspectRatio)
        self.apply_view_transform()

    def update_viewport_raster(self, layer_id):
        logger.info("Membaca ukuran viewport...")
        import time
        start = time.perf_counter()
        info = self.raster_info[layer_id]
        canvas = self.viewer.mapToScene(self.viewer.viewport().rect()).boundingRect()
        world_left  = canvas.left() + self.scene_origin_x
        world_top   = canvas.top() + self.scene_origin_y
        world_right = canvas.right() + self.scene_origin_x
        world_bot   = canvas.bottom() + self.scene_origin_y
        # logger.info(f"Viewport rect={canvas}")
        logger.info(f"Scene viewport:"
                    f"x={round(canvas.x(),2)},"
                    f"y={round(canvas.y(),2)},"
                    f"w={round(canvas.width(),2)},"
                    f"h={round(canvas.height(),2)}"
                    )
        logger.info(f"Raster size: w={info['width']}, h={info['height']}")
        import rasterio as rio
        from rasterio.windows import Window
        logger.info("Melakukan window_reading...")
        with rio.open(info["path"]) as src:
            row0, col0 = src.index(world_left, world_top)
            row1, col1 = src.index(world_right, world_bot)
            x = min(col0, col1)
            y = min(row0, row1)
            w = abs(col1 - col0)
            h = abs(row1 - row0)
            window = Window(x, y, w, h)
            if src.count >= 3:
                bands = src.read([1, 2, 3], window=window)
            else:
                bands = src.read(window=window)
            mask = src.read_masks(1, window=window)
            window_transform = rio.windows.transform(window, src.transform)
            logger.info(f"Window x={x}, y={y}, w={w}, h={h}")
            logger.info(f"Pixel size={round(window_transform.a,2)}")

        logger.info(f"Window read shape: {bands.shape}")
        logger.info(f"Window mask shape: {mask.shape}")
        elapsed = time.perf_counter() - start
        logger.info(f"window reading time -> {elapsed:.3f}s")
        img = self.prepare_raster(
            bands,
            mask,
            info["dtype"],
            info["count"],
            info["nodata"],
            info["is_prediction"]
        )
        final_transform = QTransform(
            window_transform.a, window_transform.b, 
            window_transform.d, window_transform.e, 
            window_transform.c - self.scene_origin_x, window_transform.f - self.scene_origin_y
        )
        logger.info(f"img shape={img.shape if hasattr(img,'shape') else 'unknown'}")
        # logger.info(f"Window transform={window_transform}")
        # logger.info(f"Final window transform={final_transform}")
        logger.info("Menampilkan hasil window_reading...")
        self.display_raster(layer_id, img, final_transform, init_view=False)

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
        self.trigger_update_overview_level()

    def zoom_out(self):
        self._zoom -= 1
        self.viewer.scale(0.8, 0.8)
        self.trigger_update_overview_level()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.trigger_update_overview_level()
    
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
        if event.button() == Qt.MouseButton.MiddleButton:
            logger.info("Mode pan sementara ON")
            self._middle_pan = True
            self.viewer.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.viewer.setCursor(Qt.ClosedHandCursor)
            self.viewer.viewport().setCursor(Qt.ClosedHandCursor)

            fake_event = QMouseEvent(
                QEvent.MouseButtonPress,
                event.localPos(),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                event.modifiers()
            )
            super().mousePressEvent(fake_event)
            return
        
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
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            logger.info("Mode pan sementara off")
            self._middle_pan = False
            self.viewer.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.viewer.setCursor(Qt.ArrowCursor)
            self.viewer.viewport().setCursor(Qt.ArrowCursor)

            fake_event = QMouseEvent(
                QEvent.MouseButtonRelease,
                event.localPos(),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.NoButton,
                event.modifiers()
            )
            super().mouseReleaseEvent(fake_event)
            return
        super().mouseReleaseEvent(event)

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
                        "Filename": info.get("name", "-"),
                        "Source": info.get("path", "-"),
                        "Type": "Raster",
                        "Data Type (DType)": info.get("dtype", "Unknown"),
                        "CRS": info.get("crs", "Unknown"),
                        "NoData Value": info.get("nodata", "None"),
                        "Resolution": info.get("res", "Unknown"), 
                        "Legend": info.get("legend", {}),
                        "Stats": info.get("stats", {})
                    })
        # Jika item adalah vektor
        elif isinstance(item, QGraphicsItemGroup):
            info = self.vector_info.get(layer_id, {})
            metadata.update({
                        "Filename": info.get("name", "-"),
                        "Source": info.get("path", "-"),
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
                logger.info(f"Polygon yang dibuat: {self.list_poly}")
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