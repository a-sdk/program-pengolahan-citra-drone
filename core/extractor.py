from core.logic.modul_ekstraksi import ekstrak_rerata_piksel
import logging
logger = logging.getLogger(__name__)

class Extractor:
    """
    Kelas untuk ekstrak rerata piksel citra.
    """
    def __init__(self):
        self.result = None

    def run(self, shp_path, input_folder, output_folder):
        logger.info("Memulai proses ekstraksi...") 
        try:
            self.result = ekstrak_rerata_piksel(shp_path, input_folder, output_folder) 
            return self.result
        except Exception as e:
            self.status = "Error"
            logger.error(f"ERROR: {type(e).__name__}: {e}", exc_info=True)
            return None