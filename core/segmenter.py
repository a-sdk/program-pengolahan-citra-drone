from core.logic.modul_transformasi import proses_segmentasi
import logging 
logger = logging.getLogger(__name__)

class Segmenter:
    """
    Kelas untuk segmentasi citra.
    """
    def __init__(self):
        self.result = None

    def run(self, input_folder, ndvi_path, output_folder, check_cancel=None, on_progress=None):
        logger.info("Memulai proses segmentasi...") 
        try:
            self.result = proses_segmentasi(input_folder, ndvi_path, output_folder, check_cancel, on_progress) 
            return self.result
        except Exception as e:
            logger.error(f"ERROR: {type(e).__name__}: {e}", exc_info=True)
            return None