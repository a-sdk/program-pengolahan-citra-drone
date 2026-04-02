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

    def run(self, raw_tif_path, shp_path, n_poly, n_subpoly, model_path, scaler_path, output_folder):
        result = AnalysisResult()

        result.original_path = raw_tif_path
        multipolygon_path = self.splitter.run(shp_path, n_poly, n_subpoly, output_folder)
        if shp_path:
            clipped_path = self.clipper.run(raw_tif_path, shp_path, output_folder)
        else:
            clipped_path = raw_tif_path

        with rio.open(clipped_path) as src:
            m_green = src.read(4)
            m_red = src.read(5)
            red_edge = src.read(6)
            nir = src.read(7)
        src_nodata = src.nodata
        src_profile = src.profile
        kanal_ms = [m_green, m_red, red_edge, nir]

        transformed_path = self.transformer.run(kanal_ms, src_profile, output_folder)
        fitur = [clipped_path, transformed_path]
        segmented_path = self.segmenter.run(fitur, src_profile, output_folder)
        masked_path = self.masker.run(clipped_path, segmented_path, output_folder)
        extracted_path = self.extractor.run(multipolygon_path, masked_path, output_folder)
        classified_path = self.classifier.run(model_path, scaler_path, masked_path, output_folder)
        for disease in classified_path:
            stats = self.stats_calc.run(disease, output_folder)
        
        result.clip_path = clipped_path
        result.transform_path = transformed_path
        result.segmentation_path = segmented_path
        result.mask_path = masked_path
        result.extraction_path = extracted_path
        result.prediction_path = classified_path
        result.statistic = stats

        return result