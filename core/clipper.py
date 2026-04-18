from core.logic.modul_klip import potong_raster
import logging

logger = logging.getLogger(__name__)

class Clipper:
    """
    Kelas untuk memotong citra.
    """
    def __init__(self):
        self.result = None

    def run(self, input_folder, shp_path, output_folder):
        self.status = "Processing"
        logger.info("Memulai clipping...") 
        try:
            self.result = potong_raster(input_folder, shp_path, output_folder) 
            return self.result
        except Exception as e:
            logger.error(f"ERROR: {type(e).__name__}: {e}", exc_info=True)
            return None