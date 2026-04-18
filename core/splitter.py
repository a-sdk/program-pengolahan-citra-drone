from core.logic.modul_utilitas import buat_multipoligon
import logging
logger = logging.getLogger(__name__)

class Splitter:
    """
    Kelas untuk memecah poligon.
    """
    def __init__(self):
        self.result = None

    def run(self, shp_path, output_folder, on_progress=None):
        logger.info("Memulai pembuatan multipoligon...") 
        try:
            self.result = buat_multipoligon(shp_path, output_folder, on_progress) 
            return self.result
        except Exception as e:
            logger.error(f"ERROR: {type(e).__name__}: {e}", exc_info=True)
            return None