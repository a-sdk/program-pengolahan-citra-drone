import fiona
import geopandas as gpd

shp_path = r"C:\Users\acer_\Documents\Orthomosaic\tes aplikasi\Lahan percobaan\Hasil_Prediksi\Sebaran_Petak\Hasil_Prediksi.gpkg"
layers = gpd.list_layers(shp_path)
for i, layer in enumerate(layers):
    print(f"Layer ke-{i}: {layers}")

'''
conn = sqlite3.connect(output_gpkg)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS app_layer_metadata (
    layer_name TEXT PRIMARY KEY,
    legend_json TEXT,
    stats_json TEXT
)
""")

cur.execute("""
INSERT OR REPLACE INTO app_layer_metadata
(layer_name, legend_json, stats_json)
VALUES (?, ?, ?)
""", (
    name,
    json.dumps(legend_dict_for_this_layer),
    json.dumps(stats_dict_for_this_layer)
))

conn.commit()
conn.close()

========= BUKA =============
conn = sqlite3.connect(path)
cur = conn.cursor()

cur.execute("""
SELECT legend_json, stats_json
FROM app_layer_metadata
WHERE layer_name = ?
""", (layer_name,))

row = cur.fetchone()

legend = json.loads(row[0])
stats = json.loads(row[1])
'''