"""
Modul berisi fungsi-fungsi pembantu
yang digunakan pada program utama
"""

import os
import json
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
import rasterio as rio
import geopandas as gpd
import fiona
from shapely.geometry import Point, MultiPoint
from pyproj import database
from pyproj.aoi import AreaOfInterest
import shapely.ops as ops
from sklearn.cluster import KMeans

import logging

logger = logging.getLogger(__name__)

# Fungsi bantu pembuatan multipoligon 
def lonlat_to_utm_epsg(lon, lat):
    utm_crs_list = database.query_utm_crs_info(
        datum_name="WGS 84",
        area_of_interest=AreaOfInterest(
            west_lon_degree=lon,
            south_lat_degree=lat,
            east_lon_degree=lon,
            north_lat_degree=lat,
        ),
    )
    # Mengambil kode EPSG dari hasil pertama yang ditemukan
    return int(utm_crs_list[0].code)

def generate_grid_points(polygon, target_count):
    bounds = polygon.bounds # (minx, miny, maxx, maxy)
    area = polygon.area
    
    # Hitung jarak antar titik ideal (asumsi persegi)
    step = (area / target_count) ** 0.5
    
    x_coords = np.arange(bounds[0], bounds[2], step)
    y_coords = np.arange(bounds[1], bounds[3], step)
    
    points = []
    for x in x_coords:
        for y in y_coords:
            p = Point(x, y)
            if polygon.contains(p):
                points.append(p)
    return points
        
# Fungsi untuk membuat multipoligon (shahiban)
def buat_multipoligon(shp_path, output_folder, on_progress):
    """
    Membuat multipoligon dari shapefile poligon.

    Parameters:
        shp_path (str): Lokasi shapefile yang menjadi acuan.
        output_folder (str): Nama folder tempat hasil klip disimpan.
        
    Returns:
        str: Output path.
    """

    # print("\nMembuat multipoligon...")
    
    output_folder = f"{output_folder}/multipoligon"
    os.makedirs(output_folder, exist_ok=True)
    filename = os.path.splitext(os.path.basename(shp_path))[0]
    # print(f"Memproses file: {filename}.shp")
    
    # ========================================
    # Tahap 1: Membaca & Konversi CRS
    # ========================================
    if on_progress:
        on_progress(11, f"Loading polygon crs...")
    polygons = gpd.read_file(shp_path)
    crs_asal = polygons.crs.to_string()
    if polygons.crs is None:
        raise ValueError(f"File {filename} tidak memiliki CRS. Harap periksa file.")

    if polygons.crs.is_geographic:
        centroid = polygons.unary_union.centroid
        epsg_code = lonlat_to_utm_epsg(centroid.x, centroid.y)
        polygons = polygons.to_crs(epsg=epsg_code)
        logger.info(f"CRS diubah dari {crs_asal} ke UTM (EPSG:{epsg_code})")
    else:
        logger.info(f"CRS sudah proyeksi: ({str(polygons.crs).upper()})")

    # Menentukan jumlah komponen poligon berdasarkan luas 
    with fiona.open(shp_path) as shp:
        jml_poligon = len(shp)
    poly_area = polygons.geometry.area.sum()
    subpoly_area = 0.5 #m2
    jml_komponen = (poly_area/subpoly_area).astype(int)
    jml_cluster = jml_poligon * jml_komponen
    logger.info(f"Terdapat {jml_poligon} poligon, total luasan: {poly_area:.2f} m2")
    logger.info(f"Jumlah komponen: {jml_komponen}")
    output_intersection = os.path.join(output_folder, f"{filename}_{jml_cluster}_part.shp")
    # ========================================
    # Tahap 2: Generate Random Points
    # ========================================
    if on_progress:
        on_progress(12, f"Generating random points...")
    point_count = jml_cluster * 3
    areas = polygons.area
    total_area = areas.sum()
    proportions = (areas / total_area) * point_count

    int_parts = proportions.astype(int)
    residuals = proportions - int_parts
    remaining = point_count - int_parts.sum()
    extra_idx = residuals.nlargest(remaining).index

    int_parts.loc[extra_idx] += 1

    all_points = []
    for idx, row in polygons.iterrows():
        pts = generate_grid_points(row.geometry, int_parts[idx])
        all_points.extend(pts)

    gdf_points = gpd.GeoDataFrame(geometry=all_points, crs=polygons.crs)
    # print(f"{len(gdf_points)} titik acak dihasilkan")

    # ========================================
    # Tahap 3: K-Means Clustering
    # ========================================
    if on_progress:
        on_progress(13, f"Clustering points...")
    coords = [(p.x, p.y) for p in gdf_points.geometry]
    kmeans = KMeans(n_clusters=jml_cluster, random_state=42, n_init=20)
    gdf_points["CLUSTER_ID"] = kmeans.fit_predict(coords)
    # print("K-Means clustering selesai")

    # ========================================
    # Tahap 4: Aggregate per Cluster
    # ========================================
    if on_progress:
        on_progress(14, f"Generating aggregates...")
    agg = gdf_points.dissolve(by="CLUSTER_ID", aggfunc="first").reset_index()
    # print("Aggregate selesai")

    # ========================================
    # Tahap 5: Hitung Centroid
    # ========================================
    if on_progress:
        on_progress(15, f"Calculating centroids...")
    agg["geometry"] = agg.geometry.centroid
    centroids = agg.copy()
    # print(f"{len(centroids)} centroid dihasilkan")

    # ========================================
    # Tahap 6: Voronoi Polygon
    # ========================================
    if on_progress:
        on_progress(16, f"Generating voronoi polygons...")
    points = MultiPoint(list(centroids.geometry))
    # buffer_union = centroids.buffer(100).unary_union
    boundary = polygons.unary_union.envelope.buffer(500) # buffer_union.convex_hull

    vor = ops.voronoi_diagram(points, envelope=boundary, tolerance=0)
    polys = [poly.buffer(0) for poly in vor.geoms if poly.is_valid and not poly.is_empty]

    gdf_voronoi = gpd.GeoDataFrame(geometry=polys, crs=centroids.crs)
    gdf_voronoi = gpd.sjoin_nearest(
        gdf_voronoi, centroids, how="left", distance_col="dist"
    )

    # print("Voronoi polygons selesai")

    # ========================================
    # Tahap 7: Intersection
    # ========================================
    if on_progress:
        on_progress(19, f"Performing intersection...")
    if polygons.crs != gdf_voronoi.crs:
        gdf_voronoi = gdf_voronoi.to_crs(polygons.crs)
        # print("CRS berbeda, disamakan dulu.")

    gdf_inter = gpd.overlay(polygons, gdf_voronoi, how="intersection")
    gdf_inter = gdf_inter[
        ~gdf_inter.geometry.is_empty & gdf_inter.geometry.is_valid
    ]
    gdf_inter = gdf_inter.drop(columns=['index_right'])
    # Menyiapkan kolom untuk prediksi model
    gdf_inter["no_urut"] = gdf_inter.groupby("id").cumcount() + 1
    # === Simpan langsung ke folder utama tanpa subfolder ===
    gdf_inter.to_file(output_intersection, driver="ESRI Shapefile")

    # print(f"Intersection selesai")

    return output_intersection

# Fungsi untuk menyimpan array NumPy ke dalam file GeoTIFF
def simpan_raster(input_raster, profile, output_folder, output_filename, nilai_nodata=None):
    """
    Menyimpan array NumPy sebagai file GeoTIFF ke folder yang ditentukan.

    Parameters:
        input_raster (np.ndarray): Array NumPy yang akan disimpan.
        profile (dict): Metadata raster dari file sumber.
        output_folder (str): Nama folder tempat file akan disimpan.
        output_filename (str): Nama file output, termasuk ekstensi.
        
    Returns:
        str: Output path.
    """
    # Gabungkan nama folder dan nama file
    output_path = os.path.join(output_folder, output_filename)

    # Pastikan folder output ada, jika tidak, buat folder baru
    os.makedirs(output_folder, exist_ok=True)

    # Perbarui profil untuk file output
    profile.update(  
        count=1,
        driver="GTiff"
    )
    if nilai_nodata is not None:
        profile.update(nodata=nilai_nodata)
        
    with rio.open(output_path, 'w', **profile) as dest:
        dest.write(input_raster, 1)

    # print(f"File {output_filename} berhasil disimpan di {output_folder}")
    return output_path

# Fungsi untuk menentukan threshold secara otomatis
def otsu_threshold(input_raster, jumlah_bin=256, rentang_nilai=(-1, 1)):
    """
    Menghitung threshold untuk masking raster.

    Parameters:
        input_raster (np.ndarray): Data raster yang akan dihitung thresholdnya.
        jumlah_bin (int): Jumlah bin histogram.
        rentang_nilai (str): Nilai min dan max yang ada pada data raster.
        
    Returns:
        float: Nilai threshold.
    """
    # Histogram dan probabilitas
    hist, bin_edges = np.histogram(input_raster.ravel(), bins=jumlah_bin, range=rentang_nilai)
    prob = hist.astype(float) / hist.sum()

    # Bin center
    bin_mids = (bin_edges[:-1] + bin_edges[1:]) / 2

    # Probabilitas kumulatif (q1) dan mean kumulatif (mu1)
    q1 = np.cumsum(prob)
    mu1 = np.cumsum(prob * bin_mids)

    # Total mean
    global_mean = mu1[-1]

    # Kelas 2
    q2 = 1 - q1
    mu2 = global_mean - mu1

    # Hindari pembagian dengan nol
    valid = (q1 > 0) & (q2 > 0)

    mean1 = np.zeros_like(mu1)
    mean2 = np.zeros_like(mu1)

    mean1[valid] = mu1[valid] / q1[valid]
    mean2[valid] = mu2[valid] / q2[valid]

    # Variansi antar kelas
    selisih_var = q1 * q2 * (mean1 - mean2) ** 2

    # Ambil threshold dengan variansi antar kelas maksimum
    nilai_terbaik = np.argmax(selisih_var * valid) 
    threshold = bin_mids[nilai_terbaik]

    return threshold

# Fungsi menampilkan histogram 
def tampilkan_histogram(nama, data, nilai_threshold):
    """
    Menampilkan histogram dari hasil perhitungan transformasi indeks vegetasi.

    Parameters:
        nama (str): Nama transformasi indeks vegetasi yang digunakan.
        data (np.ndarray): Array NumPy yang akan ditampilkan.
        nilai_threshold (float): Batas yang ditentukan.
        
    Returns:
        None.
    """
    # Membuat histogram untuk menampilkan data piksel SAVI
    print(f"Menampilkan histogram {nama}...")
    plt.figure(figsize=(10, 6))
    plt.hist(data, bins=100, color='lightgreen', edgecolor='black')
    plt.title(f"Histogram Nilai {nama}")
    plt.xlabel(f"Nilai {nama}")
    plt.ylabel("Frekuensi Piksel")
    plt.grid(True, alpha=0.5)
    plt.axvline(x=nilai_threshold, color='r', linestyle='--', label=f"Batas = {nilai_threshold}")
    plt.legend()
    plt.show()

# Fungsi menumpuk semua fitur (band)
def tumpuk_fitur(lst_fitur, output_folder, output_filename, nilai_nodata=0):
    """
    Menumpuk seluruh band atau fitur menjadi array Numpy besar.

    Parameters:
        lst_fitur (list): List fitur-fitur yang akan ditumpuk.
        output_folder (str): Nama folder tempat file akan disimpan.
        output_filename (str): Nama file output, termasuk ekstensi.
        nilai_nodata (float): Nilai nodata raster.

    Returns:
        str: Output path.
    """
    # Gabung nama folder dan file
    output_path = os.path.join(output_folder, output_filename)
    os.makedirs(output_folder, exist_ok=True)
    # Baca semua file dan kumpulkan datanya
    feature_stack = []
    profile = None 

    for fitur in lst_fitur:
        with rio.open(fitur) as src:
            if profile is None:
                profile = src.profile
                profile.update(
                    dtype="float32",
                    nodata=nilai_nodata
                ) 
            # Baca semua band dari file ini
            feature_stack.append(src.read().astype("float32"))

    # Gabungkan semua data menjadi satu array NumPy besar
    full_stack_array = np.vstack(feature_stack)

    # Perbarui profile untuk file stack baru
    total_bands = full_stack_array.shape[0]
    profile.update(count=total_bands, nodata=nilai_nodata) 

    # Tulis ke file stack baru
    with rio.open(output_path, 'w', **profile) as dst:
        dst.write(full_stack_array)

    print(f"Tumpukan fitur berhasil disimpan di: {output_folder}")
    return output_path

# Fungsi untuk menghitung sebaran penyakit per rumpun
def hitung_sebaran_rumpun(input_folder, legend_dict):
    """
    Menghitung sebaran penyakit.
    
    Parameters:
        input_folder (str): Lokasi file GeoTIFF hasil prediksi model.
        penyakit (str): Nama penyakit.

    Returns:
        None.
    """
    from path_config import InfoRegistry
    nf = os.path.splitext(os.path.basename(input_folder))[0]
    penyakit = nf.split("_")[-1]
    print(f"\nMenghitung sebaran penyakit {penyakit.title()}...")
    with rio.open(input_folder) as src:
        data = src.read(1)
        nodata = src.nodata
    # Mengecualikan nodata
    mask_valid = (data != nodata)
    valid_data = data[mask_valid]
    # Menghitung total piksel valid
    jml_data_valid = valid_data.size
    # Mengambil semua nilai unik
    counts = {k: v for k, v in zip(*np.unique(data, return_counts=True))}
    labels = [info["label"] for info in legend_dict.values()]
    # Menghitung persentase
    stats = {k: round((counts.get(i+1, 0) / jml_data_valid) * 100, 2) for i, k in enumerate(labels)}

    # Mengambil nilai untuk logika
    val_1 = stats.get(labels[0], 0)
    val_2 = stats.get(labels[1], 0)
    val_3 = stats.get(labels[2], 0)
    val_4 = stats.get(labels[3], 0)
    val_ = val_3 + val_4 
    # Logika Rekomendasi
    print("-" * 30)
    if val_ > val_1 and val_ > val_2:
        # recom = "Tingkat keparahan tinggi, segera lakukan tindakan pengendalian!"
        recom = InfoRegistry.get_info("disease", "severe")
        # print(f"Rekomendasi: {recom}")
    elif val_2 > val_1 and val_2 > val_ :  
        # recom = "Lakukan pemantauan rutin dan tindakan pencegahan." 
        recom = InfoRegistry.get_info("disease", "low")
        # print(f"Rekomendasi: {recom}")
    else:
        # recom = "Kondisi Aman: Vegetasi mayoritas dalam keadaan sehat."
        recom = InfoRegistry.get_info("disease", "healthy")
        # print(f"{recom}")

    stats["rekomendasi"] = recom

    legend_json = json.dumps(legend_dict)
    stats_json = json.dumps(stats)

    # Menyimpan legenda dan stats sebagai metadata
    with rio.open(input_folder, "r+") as dest:
        dest.update_tags(
            LEGEND=legend_json,
            STATS=stats_json
            )
    return stats
       
# Fungsi untuk menghitung sebaran per petak
def hitung_sebaran_petak(gpkg_path, legend_dict):
    from path_config import InfoRegistry
    """
    Menghitung sebaran penyakit.
    
    Parameters:
        gpkg_path (str): Lokasi shapefile hasil prediksi model.
        penyakit (str): Nama penyakit.

    Returns:
        dict: Hasil analisis.
    """
    try:
        layers = fiona.listlayers(gpkg_path)
    except Exception as e:
        logger.info(f"ERROR: {e}")
        return None
    # Siapkan tabel database gpkg
    conn = sqlite3.connect(gpkg_path)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS app_layer_metadata (
        layer_name TEXT PRIMARY KEY,
        legend_json TEXT,
        stats_json TEXT
    )
    """)
    hasil = {}
    
    # Hitung sebaran per nama layer
    for layer_name in layers:
        # print(f"\n=== Menganalisis Layer: {layer_name} ===")
        # Membaca layer spesifik
        gdf = gpd.read_file(gpkg_path, layer=layer_name)
        
        if "preds" not in gdf.columns:
            print(f"Kolom 'preds' tidak ditemukan di layer {layer_name}")
            continue

        data = gdf["preds"]
        jml_data = len(data)
        
        if jml_data == 0:
            print(f"Tidak ada data pada layer {layer_name}")
            continue

        stats = {}
        if layer_name == "water":
            # LOGIKA REGRESI
            for i, info in legend_dict.items():
                low, high = info["range"]
                # Menghitung berapa banyak nilai yang masuk dalam rentang ini
                count = data[(data >= low) & (data < high)].count()
                hasil_persen = round((count / jml_data) * 100, 2)
                stats[info["label"]] = hasil_persen
        else:
            # LOGIKA KLASIFIKASI
            counts = data.value_counts()
            for i, info in legend_dict.items():
                jumlah_spesifik = counts.get(i, 0)
                hasil_persen = round((jumlah_spesifik / jml_data) * 100, 2)
                stats[info["label"]] = hasil_persen

        labels = [info["label"] for info in legend_dict.values()]
        # Logika Rekomendasi
        val_1 = stats.get(labels[0], 0)
        val_2 = stats.get(labels[1], 0)

        if len(labels) == 3: # Nutrisi (kurang, cukup, berlebih)
            val_3 = stats.get(labels[2], 0)
            val_ = val_2 + val_3 # gabungan cukup + berlebih
            if val_1 > val_2 and val_1 > val_3:
                recom = InfoRegistry.get_info("nutrient", "deficit")
            elif val_2 > val_1 and val_2 > val_3:
                recom = InfoRegistry.get_info("nutrient", "adequate")
            else:
                recom = InfoRegistry.get_info("nutrient", "excess")
        
        elif len(labels) == 4: # Penyakit (sehat, ringan, sedang, parah)
            val_3 = stats.get(labels[2], 0)
            val_4 = stats.get(labels[3], 0) # kelas parah
            val_ = val_3 + val_4 # gabungan sedang + parah

            if val_ > val_1 and val_ > val_2:
                recom = InfoRegistry.get_info("disease", "severe")
                # recom = "Tingkat keparahan tinggi, segera lakukan tindakan pengendalian!"
            elif val_2 > val_1 and val_2 > val_: 
                recom =  InfoRegistry.get_info("disease", "low")
                # recom = "Lakukan pemantauan rutin dan tindakan pencegahan."  
            else:
                recom = InfoRegistry.get_info("disease","healthy")
                # recom = "Kondisi Aman: Vegetasi mayoritas dalam keadaan sehat."
 
        elif len(labels) == 5: # Air (rentang)
            val_3 = stats.get(labels[2], 0)
            val_4 = stats.get(labels[3], 0) 
            val_5 = stats.get(labels[4], 0) 
            val_ = val_4 + val_5 
            if val_1 > val_2 + val_3 and val_1 > val_:
                recom = InfoRegistry.get_info("water", "adequate")
            elif val_2 + val_3 > val_ and val_2 + val_3 > val_1:
                recom = InfoRegistry.get_info("water", "mid")
            elif val_ > val_2 + val_3 and val_ > val_1:
                recom = InfoRegistry.get_info("water", "dry")
        # Simpan hasil per layer ke dictionary utama
        stats["rekomendasi"] = recom
        legend = legend_dict
        
        # Masukkan ke database
        cur.execute("""
        INSERT OR REPLACE INTO app_layer_metadata
        (layer_name, legend_json, stats_json)
        VALUES (?, ?, ?)
        """, (
            layer_name,
            json.dumps(legend),
            json.dumps(stats)
        ))
        hasil[layer_name] = stats

    # Menutup database
    conn.commit()
    conn.close()
    return hasil
    

if __name__ == "__main__":
    geotiff_file = r"C:\Users\acer_\Documents\laporan skrpsi\Pengujian\Hasil\Lahan Uji_Files\Klip\Lahan Uji_clip.tif"
    koords_verteks = r"C:\Users\acer_\Documents\laporan skrpsi\Pengujian\Hasil\Lahan Uji_Files\Koordinat Vertek"
    hasil_prediksi = r"C:\Users\acer_\Documents\laporan skrpsi\Pengujian\Hasil\Lahan Uji_Files\Deteksi\Hasil_Prediksi.xlsx"
    folder_hasil = r"C:\Users\acer_\Documents\laporan skrpsi\Pengujian\Hasil\Lahan Uji_Files\Deteksi" 