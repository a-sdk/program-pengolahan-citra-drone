from app.result_model import AnalysisResult
from gui.worker import WorkerHelper
from core.clipper import Clipper
from core.transformer import Transformer, VegetationIndicesCalculator
from core.segmenter import Segmenter
from core.masker import Masker
from core.extractor import Extractor
from core.classifier import WaterPlotClassifier
from core.splitter import Splitter
from core.stats_calculator import WaterPlotCalculator

import logging

logger = logging.getLogger(__name__)

class WaterAnalysis:
    def __init__(self):
        self.splitter = Splitter()
        self.clipper = Clipper()
        self.transformer = Transformer()
        self.vi_calculator = VegetationIndicesCalculator()
        self.segmenter = Segmenter()
        self.masker = Masker()
        self.extractor = Extractor()
        self.classifier = WaterPlotClassifier()
        self.stats_calc = WaterPlotCalculator()
        self.on_progress = None
        self.on_error = None
        self.on_finished = None

    def run(self, raw_tif_path, shp_path, output_folder, hooks=None):
        result = AnalysisResult()
        h = WorkerHelper(hooks)
  
        try:
            result.original_path = raw_tif_path
            if h.cancelled(): return None
            h.progress(10, "Generating multi polygon...")
            multipolygon_path = self.splitter.run(
                shp_path, 
                output_folder, 
                on_progress=h.progress
                )
            if h.cancelled(): return None
            h.progress(20, "Loading raster file...")
            if shp_path:
                clipped_path = self.clipper.run(raw_tif_path, shp_path, output_folder)
            else:
                clipped_path = raw_tif_path
            if h.cancelled(): return None
            h.progress(30, "Transforming with NDVI...")
            transformed_path = self.transformer.run(clipped_path, output_folder)
            if h.cancelled(): return None
            h.progress(40, "Separating vegetation...")
            segmented_path = self.segmenter.run(
                clipped_path, 
                transformed_path, 
                output_folder, 
                check_cancel=h.cancelled,
                on_progress=h.progress
                )
            if h.cancelled(): return None
            h.progress(50, "Masking raster...")
            masked_path = self.masker.run(clipped_path, segmented_path, output_folder)
            if h.cancelled(): return None
            h.progress(60, "Extracting pixel...")
            extracted_path = self.extractor.run(multipolygon_path, masked_path, output_folder)
            if h.cancelled(): return None
            h.progress(70, "Calculating vegetation indices...")
            calculated_path = self.vi_calculator.run(extracted_path, output_folder)
            if h.cancelled(): return None
            h.progress(80, "Identifying water availability...")
            classified_path = self.classifier.run(
                input_folder=calculated_path, 
                shp_path=multipolygon_path,
                output_folder=output_folder, 
                check_cancel=h.cancelled, 
                on_progress=h.progress
                )    
            if h.cancelled(): return None
            h.progress(90, "Calculating stats...")
            stats = []
            if h.cancelled(): return None
            stats = self.stats_calc.run(classified_path)
            h.progress(95, "Done")
            # logger.info(f"Stats: {stats}")
            result.clip_path = clipped_path
            result.transform_path = transformed_path
            result.segmentation_path = segmented_path
            result.mask_path = masked_path
            result.extraction_path = extracted_path
            result.prediction_path = classified_path
            if hooks and "on_finished" in hooks:
                hooks["on_finished"](result)
            return result
        
        except Exception as e:
            h.error(str(e))
            logger.error(f"Terjadi kesalahan: {str(e)}")
            return None
        
        finally:
            h.progress(100, "Done")
            logger.info("Semua proses selesai!")