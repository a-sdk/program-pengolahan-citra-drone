from core.logic.modul_klasifikasi import (
    deteksi_penyakit_rumpun, 
    deteksi_penyakit_petak,
    deteksi_air_petak,
    deteksi_nutrisi_petak
)
from path_config import AppPaths
import logging
logger = logging.getLogger(__name__)

class BaseClassifier:
    MODEL1_PATH = None
    MODEL2_PATH = None
    MODEL3_PATH = None
    SCALER1_PATH = None
    SCALER2_PATH = None
    SCALER3_PATH = None

    def __init__(self):
        self.scaler_1 = None
        self.scaler_2 = None
        self.scaler_3 = None
        self.model_1 = None
        self.model_2 = None
        self.model_3 = None
        self.result = None

    def _load_model(self):
        if self.MODEL1_PATH is None or self.SCALER1_PATH is None:
            raise ValueError("Path model belum ditentukan di child class!")
        if self.model_1 is not None:
            return
        
        import tensorflow as tf
        import joblib
        self.scaler_1 = joblib.load(self.SCALER1_PATH)
        self.model_1 = tf.keras.models.load_model(self.MODEL1_PATH, compile=False)
        if self.MODEL2_PATH is not None and self.SCALER2_PATH is not None:
            self.scaler_2 = joblib.load(self.SCALER2_PATH)
            self.model_2 = tf.keras.models.load_model(self.MODEL2_PATH, compile=False)
        if self.MODEL3_PATH is not None and self.SCALER3_PATH is not None:
            self.scaler_3 = joblib.load(self.SCALER3_PATH)
            self.model_3 = tf.keras.models.load_model(self.MODEL3_PATH, compile=False)

    def run(self, input_folder, output_folder, shp_path=None, check_cancel=None, on_progress=None):
        logger.info(f"Memulai prediksi dengan {self.__class__.__name__}...")
        try:
            self.result = self._do_prediction(input_folder, output_folder, shp_path, check_cancel, on_progress)
            return self.result
        except Exception as e:
            logger.error(f"ERROR: {type(e).__name__}: {e}", exc_info=True)
            return None  
           
    def _do_prediction(self, *args, **kwargs):
            raise NotImplementedError("Child class harus mengimplementasikan method _do_prediction")
    
class PlantDiseaseClassifier(BaseClassifier):
    """
    Kelas untuk deteksi penyakit per rumpun.
    """ 
    MODEL1_PATH = AppPaths.MODELS / "disease_detection/disease_classification_model.h5"
    SCALER1_PATH = AppPaths.SCALERS / "disease_classification_scaler.joblib"
    def __init__(self):
        super().__init__()

    def _do_prediction(self, input_folder, output_folder, shp_path, check_cancel, on_progress):
        self._load_model()
        output_path = deteksi_penyakit_rumpun(
            scaler=self.scaler_1, 
            model=self.model_1, 
            input_folder=input_folder, 
            output_folder=output_folder, 
            check_cancel=check_cancel, 
            on_progress=on_progress
            )
        return output_path
    
class DiseasePlotClassifier(BaseClassifier):
    """
    Kelas untuk deteksi penyakit per plot/petak.
    """ 
    MODEL1_PATH = AppPaths.MODELS / "disease_detection/disease_classification_model.h5"
    SCALER1_PATH = AppPaths.SCALERS / "disease_classification_scaler.joblib"
    def __init__(self):
        super().__init__()

    def _do_prediction(self, input_folder, output_folder, shp_path, check_cancel, on_progress):
        self._load_model()
        output_gpkg = deteksi_penyakit_petak(
            self.scaler_1, 
            self.model_1, 
            input_folder, 
            shp_path, 
            output_folder, 
            check_cancel,
            on_progress
            )
        return output_gpkg
    
class WaterPlotClassifier(BaseClassifier):
    """
    Kelas untuk deteksi ketersedian air per plot/petak.
    """ 
    MODEL1_PATH = AppPaths.MODELS / "water_availability/water_regression_model.h5"
    SCALER1_PATH = AppPaths.SCALERS / "water_regression_polynom.joblib"
    SCALER2_PATH = AppPaths.SCALERS / "water_regression_scaler.joblib"
    def __init__(self):
        super().__init__()

    def _do_prediction(self, input_folder, output_folder, shp_path, check_cancel, on_progress):
        self._load_model()
        output_gpkg = deteksi_air_petak(
            polynom=self.scaler_1, 
            scaler=self.scaler_2,
            model_reg=self.model_1, 
            input_folder=input_folder, 
            shp_path=shp_path, 
            output_folder=output_folder, 
            check_cancel=check_cancel,
            on_progress=on_progress
            )
        return output_gpkg
    
class NutrientPlotClassifier(BaseClassifier):
    """
    Kelas untuk deteksi ketersediaan nitrogen per plot/petak.
    """ 
    MODEL1_PATH = AppPaths.MODELS / "nutrient_availability/nitrogen_classification_model.h5"
    SCALER1_PATH = AppPaths.SCALERS / "disease_classification_scaler.joblib"

    def __init__(self):
        super().__init__()

    def _do_prediction(self, input_folder, output_folder, shp_path, check_cancel, on_progress):
        self._load_model()
        output_gpkg = deteksi_nutrisi_petak(
            scaler_n=self.scaler_1, 
            scaler_p=self.scaler_1,
            scaler_k=self.scaler_1,
            model_n=self.model_1,
            model_p=self.model_1, 
            model_k=self.model_1,
            input_folder=input_folder, 
            shp_path=shp_path, 
            output_folder=output_folder, 
            check_cancel=check_cancel,
            on_progress=on_progress
            )
        return output_gpkg