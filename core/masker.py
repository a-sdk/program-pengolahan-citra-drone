from core.logic.modul_mask import mask_tumpukan_fitur
import logging 

logger = logging.getLogger(__name__)

class Masker:
    """
    Kelas untuk masking citra.
    """
    def __init__(self):
        self.result = None

    def run(self, input_folder, mask_path, output_folder):
        self.status = "Processing"
        logger.info("Memulai proses masking...") 
        try:
            self.result = mask_tumpukan_fitur(input_folder, mask_path, output_folder) 
            return self.result
        except Exception as e:
            logger.error(f"ERROR: {type(e).__name__}: {e}", exc_info=True)
            return None