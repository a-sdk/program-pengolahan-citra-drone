from core.logic.modul_utilitas import hitung_sebaran_rumpun, hitung_sebaran_petak
import logging
logger = logging.getLogger(__name__)

class StatsCalculator:
    """
    Kelas untuk menghitung sebaran per plot/petak.
    """
    def __init__(self):
        self.result = None

    def run(self, input_folder):
        logger.info("Menghitung sebaran dan memunculkan hasil...") 
        try:
            self.result = self._do_calculation(input_folder)
            return self.result
        except Exception as e:
            logger.error(f"ERROR: {type(e).__name__}: {e}", exc_info=True)
            return None 
        
    def _do_calculation(self, *args, **kwargs):
        raise NotImplementedError("Child class harus mengimplementasikan method _do_prediction")
        
class PlantCalculator(StatsCalculator):
    """
    Kelas untuk menghitung sebaran per rumpun.
    """ 
    def _do_calculation(self, input_folder):
        stats = hitung_sebaran_rumpun(input_folder)
        return stats
        
class PlotCalculator(StatsCalculator):
    """
    Kelas untuk menghitung sebaran per plot/petak.
    """ 
    def _do_calculation(self, input_folder):
        stats = hitung_sebaran_petak(input_folder)
        return stats