import numpy as np
import json
import logging
import psutil
import os
from PyQt5.QtGui import QTransform
from PyQt5.QtCore import pyqtSignal, QObject, QTimer
from app.worker import WorkerHelper
from gui.layer_manager import Layer
from path_config import AppPaths

logger = logging.getLogger(__name__)
process = psutil.Process(os.getpid())

class RasterHandler(QObject):
    crsDetected = pyqtSignal(str)
    rasterUpdated = pyqtSignal(int, bool)
    originUpdated = pyqtSignal(float, float)
    def __init__(self, layer_manager):
        super().__init__()
        self.OVERVIEW_FACTORS = [2,4,8,16,32]
        self._factor = None
        self.layer_manager = layer_manager
        self.raster_info = {}
        self.scene_origin_x = None
        self.scene_origin_y = None
        self.viewport_canvas = None
        self.viewport_zoom_ratio = None
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.update_overview_level)
        self.debounce_delay = 350 #ms

    def get_raster_origin(self, xmin, ymax):
        if self.scene_origin_x is None:
            self.scene_origin_x = xmin
            self.scene_origin_y = ymax
            self.originUpdated.emit(xmin, ymax)

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
    
    def add_raster(self, name, layer_id, path, hooks=None):
        import rasterio as rio
        helper = WorkerHelper(hooks)
        filename = name.split(".")[0]
        temp_dir = AppPaths.TEMP / filename
        temp_dir.mkdir(parents=True, exist_ok=True)
        # logger.info(f"RAM: {process.memory_info().rss / 1024**2:.1f} MB")
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
                if self.scene_origin_x is None and self.scene_origin_y is None:
                    self.get_raster_origin(t.c, t.f)
                # has_overview = len(src.overviews(1)) > 0
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
                if 1 in self.OVERVIEW_FACTORS:
                    self.OVERVIEW_FACTORS.pop(0)
                if helper.cancelled(): return None
                arr = np.load(str(temp_dir/f"f{display_factor}.npz"))
                bands = arr.get("bands")
                mask = arr.get("mask")
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
                info = {
                    "Name": name,
                    "Source": path,
                    "Legend": legend_dict,
                    "Stats": stats_dict,
                    "Dtype": str(dtype),
                    "CRS": crs.to_string() if crs else "Non-Georeferenced",
                    "Count": count,
                    "Nodata": nodata,
                    "transform": t,
                    "height": h,
                    "width": w,
                    "Res": f"{pixel_width:.4f} m ({pixel_width*100:.1f} cm/px)",
                    "current_factor": display_factor,
                    "base_factor": display_factor,
                    "cache_dir": str(temp_dir),
                    "is_prediction": isPrediction
                }
                self.raster_info[layer_id] = info
        self.crsDetected.emit(crs.to_string() if crs else "Unknown")
        helper.progress(100, "Done")
        # Assign layer
        layer = Layer(
            sid=layer_id,
            name=name,
            item=img,
            layer_type="raster",
            metadata=info,
            crs=crs,
            qtransform=qt_transform
            )
        return layer

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

    def update_viewport_raster(self, layer_id):
        logger.info("Membaca ukuran viewport...")
        layer = self.layer_manager.get_layer(layer_id)
        if not layer:
            return
        import time
        start = time.perf_counter()
        canvas = self.viewport_canvas
        info = layer.metadata
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
        with rio.open(info.get("Source")) as src:
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
            info.get("Dtype"),
            info.get("Count"),
            info.get("Nodata"),
            info.get("is_prediction")
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
        # Update layer img + transform
        layer.item = img
        layer.qtransform = final_transform
        self.rasterUpdated.emit(
            layer_id,
            False
        )

    def reload_overview(self, layer_id, factor):
        from pathlib import Path
        layer = self.layer_manager.get_layer(layer_id)
        info = layer.metadata
        raster_height = info.get("height")
        raster_width = info.get("width")
        
        if factor == 1 and raster_width > 10000 and raster_height > 10000:
            self.update_viewport_raster(layer_id)
            logger.info(f"Reload layer {layer_id} -> f{factor} -> window_reading")
        elif factor != info.get("current_factor"):
            cache_dir = Path(info.get("cache_dir"))
            arr = np.load(str(cache_dir/f"f{factor}.npz"))
            bands = arr.get("bands")
            mask = arr.get("mask")

            img = self.prepare_raster(
                bands,
                mask,
                info.get("Dtype"),
                info.get("Count"),
                info.get("Nodata"),
                info.get("is_prediction")
            )
            
            img_transform = self.update_transform(
                info.get("transform"), 
                info.get("width"), 
                info.get("height"), 
                bands.shape[2],
                bands.shape[1]
            )
            # Update layer img + transform 
            layer.item = img
            layer.qtransform = img_transform
            self.rasterUpdated.emit(
                layer_id,
                False
            )
            logger.info(f"Reload layer {layer_id} -> f{factor} {bands.shape}")
        info["current_factor"] = factor     

    def update_overview_level(self):
        zoom_ratio = self.viewport_zoom_ratio
        logger.info("UPDATE OVERVIEW LEVEL!")  
        for layer_id, info in self.raster_info.items():
            logger.info(f"==== INFO LAYER {layer_id} ====")
            base_factor = info.get("base_factor")
            current_factor = self.choose_factor(base_factor, zoom_ratio)
            logger.info(f"layer={layer_id}, factor={current_factor}")
            self.reload_overview(layer_id, current_factor)

    def trigger_update_overview_level(self):
        self.debounce_timer.stop() # Stop timer
        self.debounce_timer.start(self.debounce_delay) # Mulai ulang

    def set_viewport_state(self, canvas, zoom_ratio):
        self.viewport_canvas = canvas
        self.viewport_zoom_ratio = zoom_ratio

    def remove_raster(self, layer_id):
        self.raster_info.pop(layer_id, None)
        if not self.raster_info:
            self.scene_origin_x = None
            self.scene_origin_y = None

    