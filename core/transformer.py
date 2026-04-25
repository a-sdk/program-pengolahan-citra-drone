from core.logic.modul_transformasi import persiapan_segmentasi, proses_transformasi
import logging
logger = logging.getLogger(__name__)

class Transformer:
    """
    Kelas untuk mentransformasi citra.
    """
    def __init__(self):
        self.result = None
    
    def run(self, input_folder, output_folder):
        logger.info("Memulai proses transformasi...") 
        try:
            self.result = persiapan_segmentasi(input_folder, output_folder) 
            return self.result
        except Exception as e:
            logger.error(f"ERROR: {type(e).__name__}: {e}", exc_info=True)
            return None
        
class VegetationIndicesCalculator:
    """
    Kelas untuk menghitung indeks vegetasi.
    """
    def __init__(self):
        self.result = None
    
    def run(self, input_folder, output_folder):
        logger.info("Menghitung indeks vegetasi...") 
        try:
            self.result = proses_transformasi(input_folder, output_folder) 
            return self.result
        except Exception as e:
            logger.error(f"ERROR: {type(e).__name__}: {e}", exc_info=True)
            return None