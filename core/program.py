import rasterio as rio
import json 

def ubah_tag(input_folder, legend_dict, stats_dict):
    with rio.open(input_folder, "r+") as src:
        legend_json = json.dumps(legend_dict)
        stat_json = json.dumps(stats_dict)
        tag = src.tags()
        print(tag)
        tag = src.update_tags(LEGEND=legend_json, STATS=stat_json)
        print(tag)

def buka_tag(input_folder, key1, key2):
    with rio.open(input_folder) as src:
        legenda = json.loads(src.tags()[key1])
        stats = json.loads(src.tags()[key2])
        print(legenda['Healthy'])
        print(stats)


if __name__ == "__main__":
    path = r"C:\Users\acer_\Documents\Orthomosaic\tes aplikasi\Lahan percobaan\Hasil_Prediksi\Sebaran_Rumpun\peta_sebaran_penyakit_blas.tif"
    legenda = {
            "Healthy": (0, 128, 0),
            "Low": (144, 238, 144),
            "Mild": (255, 255, 116),
            "Severe": (215, 25, 28)
        }
    stats = {
            'Healthy': 5.29, 
            'Low': 0.0, 
            'Mild': 0.41, 
            'Severe': 94.3, 
            'rekomendasi': 'High severity level, immediate action required!'
        }
    ubah_tag(path, legenda, stats)
    buka_tag(path, 'LEGEND', 'STAT')
    