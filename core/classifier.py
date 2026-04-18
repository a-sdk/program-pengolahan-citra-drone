from core.logic.modul_klasifikasi import deteksi_rumpun, deteksi_petakan
import logging
logger = logging.getLogger(__name__)

class BaseClassifier:
    MODEL_PATH = None
    SCALER_PATH = None

    def __init__(self):
        self.scaler = None
        self.model = None
        self.result = None

    def _load_model(self):
        if self.MODEL_PATH is None or self.SCALER_PATH is None:
            raise ValueError("Path model belum ditentukan di child class!")
        if self.model is not None:
            return
        
        import tensorflow as tf
        import joblib
        self.scaler = joblib.load(self.SCALER_PATH)
        self.model = tf.keras.models.load_model(self.MODEL_PATH, compile=False)
        logger.info(f"Model dimuat bertipe: {type(self.model)}")

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
    MODEL_PATH = "core/models/deteksi_penyakit/model_deteksi_penyakit.h5"
    SCALER_PATH = "core/scaler/model_deteksi_penyakit_Scaler.joblib"
    def __init__(self):
        super().__init__()

    def _do_prediction(self, input_folder, output_folder, shp_path, check_cancel, on_progress):
        self._load_model()
        output_path = deteksi_rumpun(
            self.scaler, 
            self.model, 
            input_folder, 
            output_folder, 
            check_cancel, 
            on_progress
            )
        return output_path
    
class PlotDiseaseClassifier(BaseClassifier):
    """
    Kelas untuk deteksi penyakit per plot/petak.
    """ 
    MODEL_PATH = "core/models/deteksi_penyakit/model_deteksi_penyakit.h5"
    SCALER_PATH = "core/scaler/model_deteksi_penyakit_Scaler.joblib"
    def __init__(self):
        super().__init__()

    def _do_prediction(self, input_folder, output_folder, shp_path, check_cancel, on_progress):
        self._load_model()
        output_gpkg = deteksi_petakan(
            self.scaler, 
            self.model, 
            input_folder, 
            shp_path, 
            output_folder, 
            check_cancel,
            on_progress
            )
        return output_gpkg
    
class PlotWaterClassifier(BaseClassifier):
    """
    Kelas untuk deteksi ketersedian air per plot/petak.
    """ 
    MODEL_PATH = "core/models/deteksi_penyakit/model_deteksi_penyakit.h5"
    SCALER_PATH = "core/scaler/model_deteksi_penyakit_Scaler.joblib"
    def __init__(self):
        super().__init__()

    def _do_prediction(self, input_folder, output_folder, shp_path, check_cancel, on_progress):
        self._load_model()
        output_gpkg = deteksi_petakan(
            self.scaler, 
            self.model, 
            input_folder, 
            shp_path, 
            output_folder, 
            check_cancel,
            on_progress
            )
        return output_gpkg
    
class PlotNutrientClassifier(BaseClassifier):
    """
    Kelas untuk deteksi ketersediaan nitrogen per plot/petak.
    """ 
    MODEL_PATH = "core/models/deteksi_penyakit/model_deteksi_penyakit.h5"
    SCALER_PATH = "core/scaler/model_deteksi_penyakit_Scaler.joblib"
    def __init__(self):
        super().__init__()

    def _do_prediction(self, input_folder, output_folder, shp_path, check_cancel, on_progress):
        self._load_model()
        output_gpkg = deteksi_petakan(
            self.scaler, 
            self.model, 
            input_folder, 
            shp_path, 
            output_folder, 
            check_cancel,
            on_progress
            )
        return output_gpkg