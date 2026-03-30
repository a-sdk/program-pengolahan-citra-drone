"""
PIPELINE PENGOLAHAN CITRA SATELIT LENGKAP (SINKRON MODULAR)
-------------------------------------------------------
Update: Tkinter Interactive Progress Bar & Robust Status Reading
Modifikasi: Menghilangkan label Status Aktual pada Visualisasi Peta
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import random
import re
import joblib
import warnings
import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
import rasterio as rio
import rasterio.mask
import geopandas as gpd
import shapely.ops as ops
from shapely.geometry import Point, MultiPoint, mapping
from sklearn.cluster import KMeans
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from skimage import exposure
from skimage.filters import threshold_local, gaussian
from skimage.morphology import remove_small_objects, remove_small_holes, binary_closing, disk
from scipy import ndimage
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

# =====================================================
# KUNCI KEACAKAN (REPRODUCIBILITY)
# =====================================================
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)
RS = np.random.RandomState(SEED)

warnings.filterwarnings('ignore')

# =====================================================
# 0. KONFIGURASI GLOBAL (INTERFACE TKINTER)
# =====================================================
root = tk.Tk()
root.withdraw() 
root.attributes("-topmost", True) 

print("Pilih file Citra (.tif)...")
RASTER_RAW = filedialog.askopenfilename(title="Pilih File Citra (.tif)", filetypes=[("TIF files", "*.tif")])

print("Pilih file Polygon (.shp)...")
SHP_UTAMA = filedialog.askopenfilename(title="Pilih File Polygon (.shp)", filetypes=[("Shapefile", "*.shp")])

if RASTER_RAW and SHP_UTAMA:
    N_CLUSTERS = simpledialog.askinteger("Input", "Masukkan jumlah multi poligon (cluster) yang diinginkan:", 
                                          parent=root, minvalue=2, maxvalue=10000, initialvalue=50)
    if not N_CLUSTERS:
        N_CLUSTERS = 50 

print("Pilih Folder Output...")
ROOT_OUTPUT = filedialog.askdirectory(title="Pilih Folder untuk Menyimpan Hasil")

PATH_MODEL_H5 = r"C:\mYdata\SKRRP\Belajar\Pengolahan_Citra_Multispektral\program_shahiban\model_prediksi_air.h5"
PATH_SCALER    = r"C:\mYdata\SKRRP\Belajar\Pengolahan_Citra_Multispektral\program_shahiban\scaler_model_prediksi_air.pkl"

CLIP_TIF      = os.path.join(ROOT_OUTPUT, "clip.tif")
MASK_TIF      = os.path.join(ROOT_OUTPUT, "mask.tif")
MULTI_FOLDER  = os.path.join(ROOT_OUTPUT, "Multi Poligon")
CSV_FINAL     = os.path.join(ROOT_OUTPUT, "Nilai_Piksel.csv")
GPKG_FINAL    = os.path.join(ROOT_OUTPUT, "Nilai_Piksel.gpkg")

BAND_NAMES = ["RED_VIS", "GREEN_VIS", "BLUE_VIS", "M_GREEN", "M_RED", "M_RE", "M_NIR"]
X_COLUMNS_AI = ['M_GREEN', 'M_RED', 'NDVI', 'NDRE', 'GNDVI', 'EVI', 'VIDVI', 'CIVE']
RED_BAND_IDX, NIR_BAND_IDX = 5, 7 

# =====================================================
# UTILS & PROGRESS BAR CLASS
# =====================================================
class ProgressWin:
    def __init__(self, title, max_val):
        self.win = tk.Toplevel()
        self.win.title(title)
        self.win.attributes("-topmost", True)
        self.win.geometry("400x120")
        self.win.resizable(False, False)
        tk.Label(self.win, text=title, font=("Arial", 10, "bold")).pack(pady=5)
        self.prog = ttk.Progressbar(self.win, orient="horizontal", length=350, mode="determinate")
        self.prog.pack(pady=5)
        self.prog["maximum"] = max_val
        self.lbl = tk.Label(self.win, text="Initializing...")
        self.lbl.pack()
        self.win.update()

    def update(self, val, msg):
        self.prog["value"] = val
        self.lbl.config(text=msg)
        self.win.update()

    def close(self):
        self.win.destroy()

def safe_div(num, denom):
    with np.errstate(divide='ignore', invalid='ignore'):
        res = num / denom
    val = np.where(np.isfinite(res), res, 0.0)
    return float(val) if np.isscalar(val) or val.size == 1 else val.astype(float)

def get_trimmed_mean(data, low_per=10, high_per=90):
    data = data[~np.isnan(data)]
    data = data[data > 0] 
    if data.size == 0: return 0.0
    low_val, high_val = np.percentile(data, low_per), np.percentile(data, high_per)
    trimmed_data = data[(data >= low_val) & (data <= high_val)]
    return float(np.mean(trimmed_data)) if trimmed_data.size > 0 else float(np.mean(data))

def normalize_robust(band):
    p1, p99 = np.percentile(band, (1, 99))
    return np.clip((band - p1) / (p99 - p1 + 1e-6), 0, 1)

def extract_number(filename):
    nums = re.findall(r"\d+", filename)
    return int(nums[0]) if nums else 0

def r_square_metric(y_true, y_pred):
    SS_res =  tf.reduce_sum(tf.square(y_true - y_pred)) 
    SS_tot = tf.reduce_sum(tf.square(y_true - tf.reduce_mean(y_true))) 
    return (1 - SS_res/(SS_tot + tf.keras.backend.epsilon()))

# =====================================================
# TAHAP 1-4: PEMROSESAN GEOSPASIAL
# =====================================================
def run_geoprocessing():
    print("\n" + "="*50 + "\n🛰️  MEMULAI PEMROSESAN CITRA (SINKRON)\n" + "="*50)
    os.makedirs(ROOT_OUTPUT, exist_ok=True)

    print(">>> TAHAP 1: CLIPPING RASTER...")
    with rio.open(RASTER_RAW) as src:
        mask_gdf = gpd.read_file(SHP_UTAMA)
        if mask_gdf.crs != src.crs: mask_gdf = mask_gdf.to_crs(src.crs)
        geoms = [geom.__geo_interface__ for geom in mask_gdf.geometry]
        out_image, out_transform = rio.mask.mask(src, geoms, crop=True)
        out_meta = src.meta.copy()
        out_meta.update({"height": out_image.shape[1], "width": out_image.shape[2], "transform": out_transform})
    with rio.open(CLIP_TIF, "w", **out_meta) as dest: dest.write(out_image)

    print(">>> TAHAP 2: MASKING VEGETASI (ADAPTIVE)...")
    with rio.open(CLIP_TIF) as src:
        img = src.read()
        profile = src.profile
    
    red_m = normalize_robust(img[RED_BAND_IDX - 1].astype(float))
    nir_m = normalize_robust(img[NIR_BAND_IDX - 1].astype(float))
    ndvi = safe_div(nir_m - red_m, nir_m + red_m)
    ndvi = np.nan_to_num(ndvi, nan=-1.0)

    ndvi_enhanced = exposure.equalize_adapthist(ndvi, kernel_size=32, clip_limit=0.02)
    ndvi_blur = gaussian(ndvi_enhanced, sigma=0.5)
    local_thresh = threshold_local(ndvi_blur, block_size=101, offset=0.01, method='gaussian')
    mask_binary = (ndvi_blur > local_thresh) & (ndvi > 0.1)
    
    mask_cleaned = binary_closing(mask_binary, disk(1))
    mask_cleaned = remove_small_objects(mask_cleaned, min_size=100)
    mask_cleaned = remove_small_holes(mask_cleaned, area_threshold=500)
    mask_cleaned = ndimage.median_filter(mask_cleaned, size=3)

    masked_img = img.copy()
    for i in range(img.shape[0]): masked_img[i][~mask_cleaned] = 0 
    profile.update(nodata=0, compress="lzw")
    with rio.open(MASK_TIF, 'w', **profile) as dst: dst.write(masked_img)

    print(f">>> TAHAP 3: GENERASI VORONOI SUB-PLOTS ({N_CLUSTERS} CLUSTERS)...")
    os.makedirs(MULTI_FOLDER, exist_ok=True)
    gdf_utama = gpd.read_file(SHP_UTAMA)
    col_id = next((c for c in gdf_utama.columns if c.lower() == 'id'), 'id')
    
    total_poly = len(gdf_utama)
    p_win = ProgressWin("Generasi Voronoi Sub-Plots", total_poly)
    for i, (_, row) in enumerate(gdf_utama.iterrows(), 1):
        p_win.update(i, f"Memproses Poligon {i} dari {total_poly}")
        id_val = row[col_id]
        single_gdf = gpd.GeoDataFrame([row], crs=gdf_utama.crs)
        poly_utm = single_gdf.to_crs(epsg=3857)
        poly = poly_utm.geometry.iloc[0]
        minx, miny, maxx, maxy = poly.bounds
        
        x_coords = RS.uniform(minx, maxx, 5000)
        y_coords = RS.uniform(miny, maxy, 5000)
        pts_raw = [Point(x, y) for x, y in zip(x_coords, y_coords)]
        pts = [p for p in pts_raw if poly.contains(p)][:2000]
        
        kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=SEED, n_init=10).fit(np.array([(p.x, p.y) for p in pts]))
        vor = ops.voronoi_diagram(MultiPoint(kmeans.cluster_centers_), envelope=poly.buffer(5).convex_hull)
        gdf_vor = gpd.GeoDataFrame(geometry=[p for p in vor.geoms], crs=poly_utm.crs)
        gdf_final = gpd.overlay(poly_utm, gdf_vor, how="intersection").to_crs(gdf_utama.crs)
        gdf_final['Original_ID'] = str(id_val)
        gdf_final.to_file(os.path.join(MULTI_FOLDER, f"Petak_{id_val}_SubPlots.shp"))
    p_win.close()
    print("    - Selesai Generasi Voronoi.")

    print(">>> TAHAP 4: EKSTRAKSI FITUR...")
    shp_files = sorted([f for f in os.listdir(MULTI_FOLDER) if f.endswith(".shp")], key=extract_number)
    results = []
    
    status_list = []
    use_excel = messagebox.askyesno("Input Status", "Apakah Anda ingin menginput nilai Status asli dari file Excel?")
    
    if use_excel:
        excel_path = filedialog.askopenfilename(title="Pilih File Excel Status", filetypes=[("Excel files", "*.xlsx *.xls")])
        if excel_path:
            df_status = pd.read_excel(excel_path)
            df_status.columns = [str(c).strip().capitalize() for c in df_status.columns]
            
            if 'Status' in df_status.columns:
                status_list = df_status['Status'].tolist()
                if len(status_list) < len(shp_files):
                    messagebox.showwarning("Peringatan", f"Baris Status di Excel ({len(status_list)}) lebih sedikit dari poligon ({len(shp_files)})!")
                    status_list += [0.0] * (len(shp_files) - len(status_list))
            else:
                messagebox.showerror("Error", "Kolom 'Status' tidak ditemukan di Excel.")
                return
        else:
            return 

    with rio.open(MASK_TIF) as src:
        bit_depth = 65535.0 if src.dtypes[0] == 'uint16' else 255.0
        total_files = len(shp_files)
        p_win = ProgressWin("Ekstraksi Fitur Citra", total_files)
        
        for i, shp_name in enumerate(shp_files):
            p_win.update(i+1, f"Menganalisis Sub-Plot {i+1} dari {total_files}")
            status_val = float(status_list[i]) if (use_excel and i < len(status_list)) else 0.0
            
            gdf = gpd.read_file(os.path.join(MULTI_FOLDER, shp_name))
            for idx, row in gdf.iterrows():
                unique_id = f"{shp_name}_{idx}"
                try:
                    out_img, _ = rio.mask.mask(src, [mapping(row.geometry)], crop=True)
                    out_img_norm = out_img.astype('float32') / bit_depth
                    
                    m = {b: get_trimmed_mean(out_img_norm[j]) for j, b in enumerate(BAND_NAMES)}
                    RV, GV, BV, MG, MR, MRE, NIR = m['RED_VIS'], m['GREEN_VIS'], m['BLUE_VIS'], m['M_GREEN'], m['M_RED'], m['M_RE'], m['M_NIR']
                    
                    L_savi, C1, C2, G_evi, L_evi = 0.5, 6.0, 7.5, 2.5, 1.0
                    msavi_inner = (2 * NIR + 1)**2 - 8 * (NIR - MR)
                    msavi_val = (2 * NIR + 1 - np.sqrt(msavi_inner)) / 2 if msavi_inner >= 0 else 0

                    indices = {
                        "NDVI":  float(safe_div(NIR - MR, NIR + MR)),
                        "NDRE":  float(safe_div(NIR - MRE, NIR + MRE)),
                        "NGRDI": float(safe_div(MG - MR, MG + MR)),
                        "GNDVI": float(safe_div(NIR - MG, NIR + MG)),
                        "NDWI":  float(safe_div(MG - NIR, MG + NIR)),
                        "SAVI":  float(safe_div(NIR - MR, NIR + MR + L_savi) * (1 + L_savi)),
                        "MSAVI": float(msavi_val),
                        "EVI":   float(np.clip(G_evi * safe_div(NIR - MR, (NIR + C1 * MR - C2 * BV + L_evi)), -1.0, 1.0)),
                        "VARI":  float(np.clip(safe_div(GV - RV, (GV + RV - BV)), -1.0, 1.0)),
                        "VIDVI": float(safe_div(2 * GV - RV - BV, 2 * GV + RV + BV)),
                        "CIVE":  float((0.441 * RV) - (0.81 * GV) + (0.385 * BV) + 18.7874),
                        "EXG":   float((2 * GV) - RV - BV),
                        "EXR":   float((1.3 * RV) - GV),
                        "VEG":   float(np.clip(GV / ((RV**0.667) * (BV**0.333)) if (RV > 0 and BV > 0) else 0, 0, 10))
                    }
                    results.append({"Unique_ID": unique_id, "Status": status_val, "geometry": row.geometry, **m, **indices})
                except: continue
        p_win.close()

    if results:
        print("\n>>> TAHAP 4.5: MENYIMPAN DATA HASIL EKSTRAKSI...")
        final_gdf = gpd.GeoDataFrame(results, crs=src.crs)
        final_df = pd.DataFrame(results).drop(columns=['geometry'])
        final_df.fillna(0, inplace=True)
        final_df.to_csv(CSV_FINAL, index=False)
        final_gdf.to_file(GPKG_FINAL, driver="GPKG")
        print(f"✅ Ekstraksi Selesai. Data disimpan di: {CSV_FINAL}")

# =====================================================
# TAHAP 5: ANALISIS AI, VISUALISASI PETA & VALIDASI
# =====================================================
def run_ai_analysis():
    print("\n" + "="*50 + "\n ANALISIS AI & VISUALISASI\n" + "="*50)
    try:
        print(">>> Memuat Model dan Scaler...")
        model = tf.keras.models.load_model(PATH_MODEL_H5, custom_objects={'r_square_metric': r_square_metric})
        scaler = joblib.load(PATH_SCALER)
        poly = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
        
        print(">>> Membaca Data...")
        df = pd.read_csv(CSV_FINAL)
        gdf = gpd.read_file(GPKG_FINAL)
        
        if 'Status' not in df.columns:
            raise KeyError("Kolom 'Status' tidak ditemukan. Pastikan proses Ekstraksi Fitur (Tahap 4) selesai sempurna.")

        print(">>> Menjalankan Prediksi...")
        x_raw = df[X_COLUMNS_AI]
        x_poly = poly.fit_transform(x_raw)
        x_scaled = scaler.transform(x_poly)
        preds = model.predict(x_scaled, verbose=0).flatten()
        
        df['y_prediksi'] = preds 
        gdf_res = gdf.merge(df[['Unique_ID', 'y_prediksi', 'Status']], on='Unique_ID')

        y_true = df['Status'].values
        y_pred = df['y_prediksi'].values
        r2_val = r2_score(y_true, y_pred)
        mae_val = mean_absolute_error(y_true, y_pred)
        print(f"📊 Skor R^2 Prediksi: {r2_val:.4f}")
        print(f"📊 Mean Absolute Error: {mae_val:.4f}")

        print(">>> Membuat Visualisasi Peta...")
        fig, ax = plt.subplots(1, 1, figsize=(16, 10))
        gdf_res.plot(column='y_prediksi', ax=ax, scheme='NaturalBreaks', k=5, legend=True, cmap='RdYlGn', 
                      edgecolor='black', linewidth=0.2, legend_kwds={'title': "Status Kecukupan Air", 'loc': 'upper left', 'bbox_to_anchor': (1.02, 1.0), 'fmt': "{:.4f}"})

        # --- MODIFIKASI: BAGIAN LOOP ax.text (LABEL STATUS) DIHAPUS ---

        ax.set_axis_on()
        ax.grid(True, linestyle='--', alpha=0.5, color='gray')
        ax.set_xlabel("Longitude / X", fontsize=10)
        ax.set_ylabel("Latitude / Y", fontsize=10)

        info_text = (f"INFORMASI PETA\n{'-'*35}\nPembuat: Shahiban / Unpad\nCRS: WGS 84 / UTM Zone 48S\n"
                      f"Lokasi: Desa Karyamukti\nWaktu: 30 Juni 2025\n{'-'*35}\nMetode: ANN Regression\nR-Square: {r2_val:.4f}\n"
                      f"Catatan: Visualisasi berdasarkan hasil Prediksi AI")

        ax.text(1.02, 0.3, info_text, transform=ax.transAxes, fontsize=11, verticalalignment='center',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=1.0, edgecolor='gray'))

        plt.title(f"Peta Prediksi Ketersediaan Air (ANN)\nFile: {os.path.basename(RASTER_RAW)}", fontsize=16, fontweight='bold', pad=25)
        plt.subplots_adjust(right=0.70) 
        plt.savefig(os.path.join(ROOT_OUTPUT, "Peta_Final_Prediksi.png"), dpi=300, bbox_inches='tight')
        plt.show()

        # Scatter Plot Validation (Tetap dipertahankan untuk evaluasi model)
        plt.figure(figsize=(8, 8))
        plt.scatter(y_true, y_pred, color='blue', alpha=0.5, label='Data Sub-Plot')
        min_v, max_v = min(min(y_true), min(y_pred)), max(max(y_true), max(y_pred))
        plt.plot([min_v, max_v], [min_v, max_v], color='red', linestyle='--', linewidth=2, label='Garis Ideal')
        plt.xlabel('Nilai Aktual (Status)', fontsize=12); plt.ylabel('Nilai Prediksi (AI)', fontsize=12)
        plt.title(f'Validasi Hasil: Aktual vs Prediksi\n$R^2$ Score: {r2_val:.4f}', fontsize=14, fontweight='bold')
        plt.legend(); plt.grid(True, linestyle=':', alpha=0.7)
        plt.savefig(os.path.join(ROOT_OUTPUT, "Scatter_Validation_R2.png"), dpi=300, bbox_inches='tight')
        plt.show()

        print(f"✅ Analisis Selesai. Hasil disimpan di folder: {ROOT_OUTPUT}")
    except Exception as e: print(f"❌ Error pada Tahap 5: {e}")

if __name__ == "__main__":
    if RASTER_RAW and SHP_UTAMA and ROOT_OUTPUT:
        run_geoprocessing()
        run_ai_analysis()
    else:
        print("❌ Pemilihan file dibatalkan.")