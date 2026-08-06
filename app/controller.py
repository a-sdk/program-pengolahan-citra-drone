from app.result_model import AnalysisResult
from app.worker import WorkerHelper
from core.logic.modul_utilitas import (
    buat_multipoligon, tumpuk_fitur, create_constant_raster
)
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
class OperationCancelledError(Exception):
    """Thrown ketika user menekan tombol cancel."""
    pass

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
            self.helper = WorkerHelper(hooks)
            self.helper.progress(5, "Checking raster...")
            import rasterio as rio
            with rio.open(tif) as src:
                if src.count < 7:
                    raise IndexError(f"Raster requires a minimum of 7 bands (found {src.count}).")
            self.result.original_path = tif
            if self.helper.cancelled(): raise OperationCancelledError("User cancelled")
            if shp:
                self.helper.progress(10, "Generating multi polygon...")
                multipolygon_path = buat_multipoligon(
                    shp, 
                    out, 
                    on_progress=self.helper.progress,
                    subpoly_area=1
                    )
            if self.helper.cancelled(): raise OperationCancelledError("User cancelled")
            self.helper.progress(20, "Loading raster file...")
            if shp:
                clipped_path = potong_raster(
                    tif, 
                    shp, 
                    out
                    )
            else:
                clipped_path = tif
            if self.helper.cancelled(): raise OperationCancelledError("User cancelled")
            # hst_band = create_constant_raster(
            #     tif=clipped_path, 
            #     value=42, 
            #     output_folder=out, 
            #     output_filename="hst.tif"
            #     )
            if self.helper.cancelled(): raise OperationCancelledError("User cancelled")
            self.helper.progress(30, "Transforming with NDVI...")
            ndrei_path, ndvi_path = persiapan_segmentasi(clipped_path, out)
            stack_path = tumpuk_fitur(
                lst_fitur=[clipped_path, ndrei_path],
                output_folder=out,
                output_filename="stack result.tif"
            )
            if self.helper.cancelled(): raise OperationCancelledError("User cancelled")
            self.helper.progress(40, "Separating vegetation...")
            segmented_path = proses_segmentasi(
                clipped_path, 
                ndvi_path, 
                out, 
                check_cancel=self.helper.cancelled,
                on_progress=self.helper.progress
                )
            if self.helper.cancelled(): raise OperationCancelledError("User cancelled")
            self.helper.progress(50, "Masking raster...")
            if self.task == "disease":
                mask_input = stack_path
            else:
                mask_input = clipped_path
            masked_path = mask_tumpukan_fitur(
                mask_input, 
                segmented_path, 
                out
                )
            if self.helper.cancelled(): raise OperationCancelledError("User cancelled")
            self.helper.progress(60, "Extracting pixel...")
            extracted_path = ekstrak_rerata_piksel(
                multipolygon_path, 
                masked_path, 
                out
                )
            if self.helper.cancelled(): raise OperationCancelledError("User cancelled")
            vi_path = self.calculate_vi(extracted_path, out)
            if self.task == "disease":
                input_data = masked_path
            elif self.task == "water" and vi_path is not None:
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
            if self.helper.cancelled(): raise OperationCancelledError("User cancelled")
            self.helper.progress(90, "Calculating stats...")
            if self.helper.cancelled(): raise OperationCancelledError("User cancelled")
            self.stats_calc.run(classified_path)
            self.helper.progress(95, "Saving results...")
            self.result.clip_path = clipped_path
            self.result.transform_path = ndvi_path
            self.result.segmentation_path = segmented_path
            self.result.mask_path = masked_path
            self.result.extraction_path = extracted_path
            self.result.prediction_path = classified_path
            self.helper.progress(100, "Done")
            logger.info("Semua proses selesai")
            return self.result

        except OperationCancelledError:
            logger.error("Proses dihentikan pengguna")
            self.helper.progress(0, "Cancelled")
            return None

        except Exception as e:
            self.helper.error(str(e))
            logger.error(f"Terjadi kesalahan: {str(e)}")
            return None

class NutrientController(BaseController):
    def __init__(self):
        super().__init__()
        self.task = "nutrient"
        self.classifier = NutrientPlotClassifier()
        self.stats_calc = NutrientPlotCalculator()

class WaterController(BaseController):
    def __init__(self):
        super().__init__()
        self.task = "water"
        self.classifier = WaterPlotClassifier()
        self.stats_calc = WaterPlotCalculator()
    
    def calculate_vi(self, input_path, out_folder):
        result_path = hitung_indeks_vegetasi(input_path, out_folder)
        return result_path

class DiseaseController(BaseController):
    def __init__(self):
        super().__init__()
        self.task = "disease"
        self.classifier = PlantDiseaseClassifier()
        self.stats_calc = PlantDiseaseCalculator()
    