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
    def __init__(self):
        super().__init__()
        self.legend = {
            1: {"label": "Healthy", "color": (0,128,0)},
            2: {"label": "Low",     "color": (144,238,144)},
            3: {"label": "Mild",    "color": (255,255,116)},
            4: {"label": "Severe",  "color": (215,25,28)}
        }

    def _do_calculation(self, input_folder):
        stats = hitung_sebaran_rumpun(input_folder, legend_dict=self.legend)
        return stats
        
class DiseasePlotCalculator(StatsCalculator):
    """
    Kelas untuk menghitung sebaran per plot/petak.
    """ 
    def __init__(self):
        super().__init__()
        self.legend = {
            1: {"label": "Healthy", "color": (0,128,0)},
            2: {"label": "Low",     "color": (144,238,144)},
            3: {"label": "Mild",    "color": (255,255,116)},
            4: {"label": "Severe",  "color": (215,25,28)}
        }

    def _do_calculation(self, input_folder):
        stats = hitung_sebaran_petak(input_folder, legend_dict=self.legend)
        return stats
    
class NutrientPlotCalculator(StatsCalculator):
    """
    Kelas untuk menghitung sebaran per plot/petak.
    """ 
    def __init__(self):
        super().__init__()
        self.legend = {
            1: {"label": "Deficit",  "color": (255,255,116)},
            2: {"label": "Adequate","color": (144,238,144)},
            3: {"label": "Excess", "color": (0,128,0)}
        }

    def _do_calculation(self, input_folder):
        stats = hitung_sebaran_petak(input_folder, legend_dict=self.legend)
        return stats

class WaterPlotCalculator(StatsCalculator):
    """
    Kelas untuk menghitung sebaran per plot/petak.
    """ 
    def __init__(self):
        super().__init__()

        self.legend = {
            # 1: {"label": "Excess",   "color": (0,128,0),    "range": (0.6, float('inf'))},
            1: {"label": "Adequate", "color": (144,238,144), "range": (0.3, float('inf'))},
            2: {"label": "Deficit",  "color": (255,255,116), "range": (-float('inf'), 0.3)}
        }

    def _do_calculation(self, input_folder):
        stats = hitung_sebaran_petak(input_folder, legend_dict=self.legend)
        return stats
