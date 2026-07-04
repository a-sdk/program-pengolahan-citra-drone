from app.result_model import AnalysisResult
from gui.worker import WorkerHelper
from core.logic.modul_utilitas import buat_multipoligon
from core.logic.modul_klip import potong_raster
from core.logic.modul_transformasi import (
    persiapan_segmentasi, proses_segmentasi, hitung_indeks_vegetasi
)
from core.logic.modul_mask import mask_tumpukan_fitur
from core.logic.modul_ekstraksi import ekstrak_rerata_piksel
from core.stats_calculator import (
    NutrientPlotCalculator, WaterPlotCalculator, PlantDiseaseCalculator
)
from core.classifier import (
    NutrientPlotClassifier, WaterPlotClassifier, PlantDiseaseClassifier
)

import logging

logger = logging.getLogger(__name__)

class BaseController:
    def __init__(self):
        self.on_progress = None
        self.on_error = None
        self.on_finished = None
        self.task = None
        self.classifier = None
        self.stats_calc = None
        self.result = AnalysisResult()

    def calculate_vi(self, input_path, out_path):
        pass

    def run(self, tif, shp, out, hooks=None):
        try:
            self.result.original_path = tif
            self.helper = WorkerHelper(hooks)
            if self.helper.cancelled(): return None
            if shp:
                self.helper.progress(10, "Generating multi polygon...")
                multipolygon_path = buat_multipoligon(
                    shp, 
                    out, 
                    on_progress=self.helper.progress,
                    subpoly_area=0.5
                    )
            if self.helper.cancelled(): return None
            self.helper.progress(20, "Loading raster file...")
            if shp:
                clipped_path = potong_raster(
                    tif, 
                    shp, 
                    out
                    )
            else:
                clipped_path = tif
            if self.helper.cancelled(): return None
            self.helper.progress(30, "Transforming with NDVI...")
            ndvi_path = persiapan_segmentasi(clipped_path, out)
            if self.helper.cancelled(): return None
            self.helper.progress(40, "Separating vegetation...")
            segmented_path = proses_segmentasi(
                clipped_path, 
                ndvi_path, 
                out, 
                check_cancel=self.helper.cancelled,
                on_progress=self.helper.progress
                )
            if self.helper.cancelled(): return None
            self.helper.progress(50, "Masking raster...")
            masked_path = mask_tumpukan_fitur(
                clipped_path, 
                segmented_path, 
                out
                )
            if self.helper.cancelled(): return None
            self.helper.progress(60, "Extracting pixel...")
            extracted_path = ekstrak_rerata_piksel(
                multipolygon_path, 
                masked_path, 
                out
                )
            if self.helper.cancelled(): return None
            vi_path = self.calculate_vi(extracted_path, out)
            if self.task == "diseases":
                input_data = masked_path
            elif self.task == "water availability" and vi_path is not None:
                input_data = vi_path
            else:
                input_data = extracted_path
            self.helper.progress(70, f"Detecting {self.task}...")
            classified_path = self.classifier.run(
                input_folder=input_data, 
                shp_path=multipolygon_path,
                output_folder=out, 
                check_cancel=self.helper.cancelled, 
                on_progress=self.helper.progress
                )    
            if self.helper.cancelled(): return None
            self.helper.progress(90, "Calculating stats...")
            if self.helper.cancelled(): return None
            self.stats_calc.run(classified_path)
            self.helper.progress(95, "Saving results...")
            self.result.clip_path = clipped_path
            self.result.transform_path = ndvi_path
            self.result.segmentation_path = segmented_path
            self.result.mask_path = masked_path
            self.result.extraction_path = extracted_path
            self.result.prediction_path = classified_path
            return self.result
        
        except Exception as e:
            self.helper.error(str(e))
            logger.error(f"Terjadi kesalahan: {str(e)}")
            return None
        
        finally:
            self.helper.progress(100, "Done")
            logger.info("Semua proses selesai!")

class NutrientController(BaseController):
    def __init__(self):
        super().__init__()
        self.task = "nutrient availability"
        self.classifier = NutrientPlotClassifier()
        self.stats_calc = NutrientPlotCalculator()

class WaterController(BaseController):
    def __init__(self):
        super().__init__()
        self.task = "water availability"
        self.classifier = WaterPlotClassifier()
        self.stats_calc = WaterPlotCalculator()
    
    def calculate_vi(self, input_path, out_folder):
        result_path = hitung_indeks_vegetasi(input_path, out_folder)
        return result_path

class DiseaseController(BaseController):
    def __init__(self):
        super().__init__()
        self.task = "diseases"
        self.classifier = PlantDiseaseClassifier()
        self.stats_calc = PlantDiseaseCalculator()
    