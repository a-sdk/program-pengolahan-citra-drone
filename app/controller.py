from app.result_model import AnalysisResult
from core.modul_klip import Clipper
from core.modul_transformasi import Transformer, Segmenter
from core.modul_mask import Masker
from core.modul_ekstraksi import Extractor
from core.modul_klasifikasi import PlantDiseaseClassifier
from core.modul_utilitas import Splitter, PlantDiseaseAnalyzer

import rasterio as rio
import os
import time

class AnalysisController:
    def __init__(self):
        self.splitter = Splitter()
        self.clipper = Clipper()
        self.transformer = Transformer()
        self.segmenter = Segmenter()
        self.masker = Masker()
        self.extractor = Extractor()
        self.classifier = PlantDiseaseClassifier()
        self.stats_calc = PlantDiseaseAnalyzer()
        self.on_progress = None
        self.on_error = None
        self.on_finished = None

    def run(self, raw_tif_path, shp_path, n_poly, n_subpoly, model_path, scaler_path, output_folder, hooks=None):
        result = AnalysisResult()
        def emit_progress(msg):
            if hooks and 'progress' in hooks: hooks['progress'](msg)
            
        def emit_error(err_msg):
            if hooks and 'error' in hooks: hooks['error'](err_msg)
        try:
            result.original_path = raw_tif_path
            emit_progress("Memulai pembuatan multipoligon...")
            multipolygon_path = self.splitter.run(shp_path, n_poly, n_subpoly, output_folder)
            emit_progress("Memulai proses pemotongan (Clipping)...")
            if shp_path:
                clipped_path = self.clipper.run(raw_tif_path, shp_path, output_folder)
            else:
                clipped_path = raw_tif_path
            emit_progress("Membaca kanal multispektral...")
            with rio.open(clipped_path) as src:
                m_green = src.read(4)
                m_red = src.read(5)
                red_edge = src.read(6)
                nir = src.read(7)
            src_nodata = src.nodata
            src_profile = src.profile
            kanal_ms = [m_green, m_red, red_edge, nir]
            emit_progress("Menghitung transformasi indeks...")
            transformed_path = self.transformer.run(kanal_ms, src_profile, output_folder)
            fitur = [clipped_path, transformed_path]
            emit_progress("Melakukan segmentasi citra...")
            segmented_path = self.segmenter.run(fitur, src_profile, output_folder)
            emit_progress("Melakukan masking citra...")
            masked_path = self.masker.run(clipped_path, segmented_path, output_folder)
            emit_progress("Melakukan ekstraksi nilai piksel citra...")
            extracted_path = self.extractor.run(multipolygon_path, masked_path, output_folder)
            emit_progress("Melakukan prediksi...")
            classified_path = self.classifier.run(model_path, scaler_path, masked_path, output_folder)
            emit_progress("Menghitung hasil analisis...")
            for disease in classified_path:
                stats = self.stats_calc.run(disease, output_folder)
                result.statistic.append(stats)
            result.clip_path = clipped_path
            result.transform_path = transformed_path
            result.segmentation_path = segmented_path
            result.mask_path = masked_path
            result.extraction_path = extracted_path
            result.prediction_path = classified_path
            if hooks and 'finished' in hooks:
                hooks['finished'](result)

            return result
        
        except FileNotFoundError as e:
            emit_error(f"File tidak ditemukan: {str(e)}")
        except Exception as e:
            emit_error(f"Terjadi kesalahan: {str(e)}")
            return None
        
        finally:
            emit_progress("Proses selesai/berhenti.")