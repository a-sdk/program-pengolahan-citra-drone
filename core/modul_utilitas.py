'''
Modul berisi fungsi-fungsi pembantu
yang digunakan pada program utama
'''
import random, os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import rasterio as rio
import geopandas as gpd
from shapely.geometry import Point, MultiPoint, Polygon
from pyproj import database
from pyproj.aoi import AreaOfInterest
from rasterio.features import rasterize
import shapely.ops as ops
from sklearn.cluster import KMeans
import matplotlib.colors as mcolor
import matplotlib.patches as mpatch

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

# Fungsi untuk meminta folder path
def ambil_file(ekstensi):
    """
    Mengambil file dengan ekstensi tertentu
    dalam suatu folder berdasarkan input.

    Parameters:
        ekstensi (str): Ekstensi file yang diambil.

    Returns:
        list: File target dan lokasi folder
    """
    while True:
        lokasi_folder = input(f"\nMasukkan path folder berisi file {ekstensi}: ").strip('"').strip("'")
        if  not os.path.isdir(lokasi_folder):
            print(f"Folder tidak ditemukan: {lokasi_folder}")
            print("Silahkan dicek dahulu.")
            continue
        folder_target = os.path.join(lokasi_folder, f"*{ekstensi}")
        file_target = glob.glob(folder_target)
        if not file_target:
            print(f"Tidak ada file {ekstensi} ditemukan di folder tersebut.")
            print("Silahkan dicek dahulu.")
        else:
            print(f"Ditemukan {len(file_target)} file {ekstensi} di folder {lokasi_folder}")
            # Menampilkan file dalam folder 
            print(f"Daftar File '{ekstensi}' dalam Folder {lokasi_folder}")
            c = 1
            for files in file_target:
                nf = os.path.splitext(os.path.basename(files))[0]
                print(f"\t {c}) {nf}")
                c += 1
            return file_target, lokasi_folder

class Splitter:
    """
    Kelas untuk memecah poligon.
    """
    def __init__(self):
        self.status = "Idle"
        self.last_result = None

    def run(self, shp_path, jml_poligon, jml_komponen, output_folder):
        self.status = "Processing"
        print(f"\nDEBUG: Memulai pembuatan multipoligon...") 
        try:
            self.last_result = self.buat_multipoligon(shp_path, jml_poligon, jml_komponen, output_folder) 
            self.status = "Done"
            return self.last_result
        except Exception as e:
            self.status = "Error"
            print(f"\nERROR: {e}")
            return None
        
    # Fungsi untuk membuat multipoligon (shahiban)
    def buat_multipoligon(self, shp_path, jml_poligon, jml_komponen,  output_folder):
        """
        Membuat multipoligon dari shapefile poligon.

        Parameters:
            shp_path (str): Lokasi shapefile yang menjadi acuan.
            jml_poligon (int): Jumlah poligon dalam satu shapefile.
            jml_komponen (int): Jumlah komponen/pecahan per poligon.
            output_folder (str): Nama folder tempat hasil klip disimpan.
            
        Returns:
            str: Output path.
        """

        print("\nMembuat multipoligon...")
        jml_cluster = jml_poligon * jml_komponen
        output_folder = f"{output_folder}/multipoligon"
        os.makedirs(output_folder, exist_ok=True)
        filename = os.path.splitext(os.path.basename(shp_path))[0]
        print(f"Memproses file: {filename}.shp")
        output_intersection = os.path.join(output_folder, f"{filename}_{jml_cluster}_komponen.shp")
        # ========================================
        # Tahap 1: Membaca & Konversi CRS
        # ========================================
        polygons = gpd.read_file(shp_path)
        crs_asal = polygons.crs.to_string()
        if polygons.crs is None:
            raise ValueError(f"File {filename} tidak memiliki CRS. Harap periksa file.")

        if polygons.crs.is_geographic:
            overall_geometry = polygons.union_all()
            centroid = overall_geometry.centroid
            epsg_code = lonlat_to_utm_epsg(centroid.x, centroid.y)
            polygons = polygons.to_crs(epsg=epsg_code)
            print(f"CRS diubah dari {crs_asal} ke UTM (EPSG:{epsg_code})")
        else:
            print(f"CRS sudah proyeksi: {polygons.crs}")

        # ========================================
        # Tahap 2: Generate Random Points
        # ========================================
        point_count = jml_cluster * 5
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
        print(f"{len(gdf_points)} titik acak dihasilkan")

        # ========================================
        # Tahap 3: K-Means Clustering
        # ========================================
        coords = [(p.x, p.y) for p in gdf_points.geometry]
        kmeans = KMeans(n_clusters=jml_cluster, random_state=42, n_init=20)
        gdf_points["CLUSTER_ID"] = kmeans.fit_predict(coords)
        print("K-Means clustering selesai")

        # ========================================
        # Tahap 4: Aggregate per Cluster
        # ========================================
        agg = gdf_points.dissolve(by="CLUSTER_ID", aggfunc="first").reset_index()
        print("Aggregate selesai")

        # ========================================
        # Tahap 5: Hitung Centroid
        # ========================================
        agg["geometry"] = agg.geometry.centroid
        centroids = agg.copy()
        print(f"{len(centroids)} centroid dihasilkan")

        # ========================================
        # Tahap 6: Voronoi Polygon
        # ========================================
        points = MultiPoint(list(centroids.geometry))
        buffer_union = centroids.buffer(100).union_all()
        boundary = buffer_union.convex_hull

        vor = ops.voronoi_diagram(points, envelope=boundary, tolerance=0)
        polys = [poly for poly in vor.geoms if poly.is_valid]

        gdf_voronoi = gpd.GeoDataFrame(geometry=polys, crs=centroids.crs)
        gdf_voronoi = gpd.sjoin_nearest(
            gdf_voronoi, centroids, how="left", distance_col="dist"
        )

        print("Voronoi polygons selesai")

        # ========================================
        # Tahap 7: Intersection
        # ========================================
        if polygons.crs != gdf_voronoi.crs:
            gdf_voronoi = gdf_voronoi.to_crs(polygons.crs)
            print("CRS berbeda, disamakan dulu.")

        gdf_inter = gpd.overlay(polygons, gdf_voronoi, how="intersection")
        gdf_inter = gdf_inter[
            ~gdf_inter.geometry.is_empty & gdf_inter.geometry.is_valid
        ]
        gdf_inter = gdf_inter.drop(columns=['index_right'])
        # Menyiapkan kolom untuk prediksi model
        gdf_inter["no_urut"] = gdf_inter.groupby("id").cumcount() + 1
        gdf_inter["blas"] = None
        gdf_inter["blb"] = None
        gdf_inter["bs"] = None
        gdf_inter["nbs"] = None
        # === Simpan langsung ke folder utama tanpa subfolder ===
        gdf_inter.to_file(output_intersection, driver="ESRI Shapefile")

        print(f"Intersection selesai")

        return output_intersection

# Fungsi untuk memeriksa ukuran raster
def cek_ukuran_raster(input_raster):
    """
    Menghitung ukuran raster dan menampilkannya di terminal/shell.

    Parameters:
        input_raster (np.ndarray): Array NumPy yang akan dihitung.
        
    Returns:
        None.
    """
    nf = os.path.basename(input_raster)
    with rio.open(input_raster) as src:
        print(f"Memeriksa bentuk...")
        band1 = src.read()
        print(f"Bentuk (shape) dari {nf} adalah {band1.shape}")

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

    print(f"File {output_filename} berhasil disimpan di {output_folder}")
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

# Fungsi untuk mengolah label penyakit 
def olah_label(input_folder, output_folder, N, z):
    """
    Mengolah label skala penyakit dengan rentang status yang berbeda tiap penyakit.

    Parameters:
        input folder (str): Lokasi file label masing-masing HST.
        output_folder (str): Nama folder tempat file akan disimpan.
        N (int): Jumlah rumpun yang diamati.
        z (int): Skala maksimum yang digunakan.



    Returns:
        str: Output path.
    """
    
    config_penyakit = {
        "blas": {
            "ringan": 2,
            "sedang": 15,
        },
        "blb": {
            "ringan": 19,
            "sedang": 35,
        },
        "bs": {
            "ringan": 2,
            "sedang": 15,
        },
        "nbs": {
            "ringan": 5,
            "sedang": 20,
        }
    }

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    files = glob.glob(os.path.join(input_folder, "*.csv"))
    
    for file in files:
        nf = os.path.splitext(os.path.basename(file))[0]
        print(f"\nMemproses file {nf}...")
        
        try:
            umur = nf.split(r" ")[1]
        except IndexError:
            umur = "unknown"

        df = pd.read_csv(file)
        grup = df.groupby("id") 
        lst_skor = []

        for id_titik, data in grup:
            baris = {"id": id_titik, "hst": umur}
            penyakit_list = ["blas", "blb", "bs", "nbs"]
            
            for nama_penyakit in penyakit_list:
                if nama_penyakit not in data.columns:
                    continue
                
                penyakit = data[nama_penyakit]
                skor = penyakit.value_counts(dropna=False)
                
                # Perhitungan IP (Intensitas Penyakit)
                sum_nv = (skor.get(1,0)*1 + skor.get(3,0)*3 + skor.get(5,0)*5 + 
                          skor.get(7,0)*7 + skor.get(9,0)*9)
                hitung_ip = round((sum_nv / (N * z)) * 100, 2)
                
                # Perhitungan DI (Disease Index)
                hitung_di = round((skor.get(3,0) + skor.get(5,0) + 
                                   skor.get(7,0) + skor.get(9,0)) / N, 2)

                # LOGIKA PENENTUAN STATUS BERDASARKAN RENTANG KHUSUS
                threshold = config_penyakit[nama_penyakit]
                
                if hitung_ip == 0:
                    status = "sehat"
                elif hitung_ip <= threshold["ringan"]:
                    status = "ringan"
                elif hitung_ip <= threshold["sedang"]:
                    status = "sedang"
                else:
                    status = "parah"

                # Penentuan Index DI (Bisa juga disesuaikan jika perlu)
                if hitung_di == 0:
                    idx = "sehat"
                elif hitung_di <= 3:
                    idx = "tahan"
                elif hitung_di <= 6:
                    idx = "rentan"
                else: 
                    idx = "sangat rentan"

                baris[f"{nama_penyakit}"] = status
                baris[f"{nama_penyakit}_ip"] = hitung_ip
                baris[f"{nama_penyakit}_di"] = idx
                
            lst_skor.append(baris)

        # Simpan Hasil
        df_hasil = pd.DataFrame(lst_skor)
        lst_kolom = ["id", "hst", "blas", "blb", "bs", "nbs", 
                     "blas_ip", "blb_ip", "bs_ip", "nbs_ip",
                     "blas_di", "blb_di", "bs_di", "nbs_di"]
        
        df_hasil = df_hasil[[c for c in lst_kolom if c in df_hasil.columns]]
        output_path = os.path.join(output_folder, f"_{nf}.csv")
        df_hasil.to_csv(output_path, index=False)
        print(f"Selesai menyimpan {output_path}")

# Fungsi untuk menggabungkan label penyakit
def gabung_label(input_folder, output_folder, output_filename):
    """
    Menggabungkan beberapa file .csv hasil olah label
    menjadi satu file .csv
    
    Parameters:
        input_folder (str): Lokasi file label masing-masing HST.
        output_folder (str): Nama folder tempat file akan disimpan.
        output_filename (str): Nama file output, termasuk ekstensi.

    Returns:
        None.
    """
    print("Menggabungkan semua label penyakit...")
    files = glob.glob(os.path.join(input_folder, "*.csv"))
    labels = []
    c = 1
    for file in files:
        nf = os.path.splitext(os.path.basename(file))[0]
        print(f"\t {c}. {nf}")
        c += 1
        umur = nf.split(r" ")[1]
        df_label = pd.read_csv(file)
        df_label["hst"] = umur
        labels.append(df_label)

    label_hasil = pd.concat(labels, axis=0, ignore_index=True)
    output_path = os.path.join(output_folder, output_filename)
    os.makedirs(output_folder, exist_ok=True)
    label_hasil.to_csv(output_path, index=False)
    print(f"File {output_filename} berhasl disimpan di: \n{output_folder}")

# Fungsi untuk menggabungkan dataset dan label
def olah_dataset(dataset_folder, label_folder, output_folder, output_filename):
    """
    Menggabungkan file dataset dengan label
    
    Parameters:
        dataset_folder (str): Lokasi folder dataset.
        label_file (str): Lokasi file gabungan label. 
        output_folder (str): Nama folder tempat file akan disimpan.
        output_filename (str): Nama file output, termasuk ekstensi.

    Returns:
        None.
    """
    files_ekstraksi = glob.glob(os.path.join(dataset_folder, "*.csv"))
    output_path = os.path.join(output_folder, output_filename)
    os.makedirs(output_folder, exist_ok=True)
    # Membaca file ke dataframe dan menambah kolom hst
    print("Membaca file hasil ekstraksi...")
    df0 = pd.read_csv(files_ekstraksi[0])
    df1 = pd.read_csv(files_ekstraksi[1])
    df2 = pd.read_csv(files_ekstraksi[2])
    df3 = pd.read_csv(files_ekstraksi[3])
    df4 = pd.read_csv(files_ekstraksi[4])
    df5 = pd.read_csv(files_ekstraksi[5])
    df6 = pd.read_csv(files_ekstraksi[6])

    df0["hst"] = 40
    df1["hst"] = 40
    df2["hst"] = 30
    df3["hst"] = 45
    df4["hst"] = 45
    df5["hst"] = 60

    # Menggabungkan semua file hasil ekstraksi
    lst_df = [df0, df1, df2, df3, df4, df5]
    df = pd.concat(lst_df, axis=0)
    df_label = pd.read_csv(label_folder)
    # Menggabungkan data dengan label
    print("Menambahkan label...")
    df_lengkap = df.merge(df_label, on=["id", "hst"])
    kolom_umur = df_lengkap.pop("hst")

    df_lengkap = df_lengkap.drop(columns=["blas_ip", "blb_ip", "bs_ip", "nbs_ip", 
                                          "blas_di", "blb_di", "bs_di", "nbs_di"])
    df_lengkap.insert(loc=2, column="HST", value=kolom_umur)
    df_lengkap.rename(columns={"id": "ID"}, inplace=True)
    print("Menyimpan dataset...")
    print(f"File {output_filename} disimpan di:\n{output_folder}")
    df_lengkap.to_csv(output_path, index=False)

# Fungsi untuk membuat peta sebaran mengacu pada koordinat verteks petakan (nurohman pupuk N)
def buat_petak_sebaran(input_geotiff, file_metadata, folder_verteks, output_folder):
    """
    Membuat peta sebaran mengacu pada koordinat verteks petakan.
    
    Parameters:
        input_geotiff (str): Lokasi file GeoTIFF hasil klip.
        file_metadata (str): Lokasi file hasil prediksi model (.xlsx). 
        folder_verteks (str): Lokasi folder koordinat verteks.
        output_folder (str): Nama folder tempat file akan disimpan.

    Returns:
        None.
    """
    ################################################################################
    # * Define Classification Mapping
    ################################################################################
    output_path = os.path.join(output_folder, "Sebaran_Petakan")
    os.makedirs(output_path, exist_ok=True)
    # Choose which classification field to use
    penyakit = ["Blas", "BLB", "BS", "NBS"]
    for nama in penyakit: 
        class_type = f"Prediksi_{nama}"
        nf_tif = f"{output_path}/{nama}.tif"
        nf_png = f"{output_path}/{nama}.png"
        # Define class labels and their corresponding RGB colors
        CLASS_COLORS = {
            "Sehat": (0, 128,00, 0),       # Green
            "Ringan": (144, 238, 144),     # Light Green
            "Agak parah": (255, 255, 116), # Light Orange
            "Parah": (215, 25, 28)         # Red
        }
        
        ################################################################################
        # * Load Metadata
        ################################################################################

        print("\n[INFO] Loading metadata...")
        metadata = pd.read_excel(file_metadata)
        print(f"[INFO] Metadata loaded: {len(metadata)} records found.")

        ################################################################################
        # * Load and Process Polygon Data
        ################################################################################

        polygons = [] # Store polygon geometries and class labels

        print("\n[INFO] Processing polygons...")
        for _, row in metadata.iterrows():
            polygon_filename = row["Nama"]
            polygon_label = str(row[class_type]).strip() # Ensure it's a string and remove whitespace
            polygon_file = f"{folder_verteks}/{polygon_filename}.csv"

            # Check if the class label is valid
            if polygon_label not in CLASS_COLORS:
                print(f"[WARNING] Unknown class '{polygon_label}' in {polygon_file}, skipping.")
                continue # Skip unknown labels

            # Load polygon coordinates
            try:
                coords = pd.read_csv(polygon_file).values
                polygon_geom = Polygon(coords)
                polygons.append({"geometry": polygon_geom, "ClassLabel": polygon_label})

                # Print polygon name, coordinates, and label
                print(f"[INFO] Polygon: {polygon_filename}")
                print(f"       Coordinates: {coords.tolist()}") # Convert numpy array to list for readability
                print(f"       Label: {polygon_label}\n")

            except Exception as e:
                print(f"[ERROR] Error loading {polygon_file}: {e}")

        print(f"[INFO] Total polygons processed: {len(polygons)}")

        ################################################################################
        # * Convert to GeoDataFrame
        ################################################################################

        # Convert the list of polygons into a GeoDataFrame with the correct coordinate system (UTM Zone 48S)
        gdf = gpd.GeoDataFrame(polygons, crs="EPSG:32748")

        ################################################################################
        # * Load GeoTIFF Raster
        ################################################################################

        print("\n[INFO] Loading raster data...")
        with rio.open(input_geotiff) as src:
            meta = src.meta.copy()
            meta.update(dtype=rio.uint16, count=src.count, nodata=0) # Ensure original uint16 format is retained

            # Read original bands
            bands = src.read()
            height, width = src.height, src.width
            print(f"[INFO] Raster size: {width} x {height}")

        ################################################################################
        # * Rasterize Polygons onto the GeoTIFF
        ################################################################################

        print("\n[INFO] Rasterizing polygons...")
        for i, (geom, class_label) in enumerate(zip(gdf.geometry, gdf["ClassLabel"])):
            r, g, b = CLASS_COLORS[class_label] # Get RGB values
            mask = rasterize([(geom, 1)], out_shape=(height, width), transform=src.transform, fill=0, dtype=np.uint8)
            
            bands[0] = np.where(mask > 0, r * 257, bands[0]) # Scale 255 to 65535
            bands[1] = np.where(mask > 0, g * 257, bands[1])
            bands[2] = np.where(mask > 0, b * 257, bands[2])
            print(f"[INFO] Rasterized polygon {i+1}/{len(gdf)}: {class_label}")

        ################################################################################
        # * Save Classified Raster as GeoTIFF
        ################################################################################
        
        print("\n[INFO] Saving classified GeoTIFF...")
        with rio.open(nf_tif, "w", **meta) as dst:
            dst.write(bands)
        print(f"[SUCCESS] RGB GeoTIFF saved at {output_path}")

        ################################################################################
        # * Convert Raster to PNG for Visualization
        ################################################################################

        print("\n[INFO] Generating PNG output...")
        rgb_image = np.stack([bands[0] // 257, bands[1] // 257, bands[2] // 257], axis=-1).astype(np.uint8)
        alpha_channel = np.where(np.sum(rgb_image, axis=-1) > 0, 255, 0).astype(np.uint8) # Set transparent background
        rgba_image = np.dstack([rgb_image, alpha_channel])

        plt.imsave(nf_png, rgba_image, format='png')
        print(f"[SUCCESS] PNG image saved at {output_path}")
        print(f"Selesai. Peta sebaran {nama} berhasil dibuat!")


    print(f"\nBerhasil membuat {len(penyakit)} peta sebaran penyakit.")

class PlantDiseaseAnalyzer:
    """
    Kelas untuk memunculkan hasil analisis per rumpun.
    """ 
    def __init__(self):
        self.status = "Idle"
        self.last_result = None

    def run(self, input_folder, output_folder):
        self.status = "Processing"
        print(f"\nDEBUG: Menghitung sebaran dan memunculkan hasil...") 
        try:
            self.tampilkan_penyakit_rumpun(input_folder, output_folder)
            self.last_result = self.hitung_sebaran_rumpun(input_folder) 
            self.status = "Done"
            return self.last_result
        except Exception as e:
            self.status = "Error"
            print(f"\nERROR: {e}")
            return None 
        
    # Fungsi menampilkan hasil prediksi model per rumpun
    def tampilkan_penyakit_rumpun(self, input_folder, output_folder):
        """
        Menampilkan peta sebaran pada grafik.
        
        Parameters:
            input_folder (str): Lokasi file GeoTIFF hasil prediksi model.
            penyakit (str): Nama penyakit.

        Returns:
            None.
        """
        nf = os.path.splitext(os.path.basename(input_folder))[0]
        penyakit = nf.split("_")[-1]
        print(f"\nMenampilkan peta sebaran penyakit {penyakit.title()}...")
        os.makedirs(output_folder, exist_ok=True)
        alpha = "#00000000"
        hg = "#008000ff"
        ht = "#90ee90ff"
        kuning = "#ffff74ff"
        merah = "#d7191cff"
        warna = [alpha, hg, ht, kuning, merah]
        cmaps = mcolor.ListedColormap(warna)

        bounds = np.arange(-0.5, 5, 1)
        norms = mcolor.BoundaryNorm(bounds, 5)
        patches = [
            mpatch.Patch(color=hg, label="Sehat", ec="black"),
            mpatch.Patch(color=ht, label="Ringan", ec="black"),
            mpatch.Patch(color=kuning, label="Sedang", ec="black"),
            mpatch.Patch(color=merah, label="Parah", ec="black")
        ]
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        ax.legend(handles=patches, loc="lower right", bbox_to_anchor=(1, 1), title="Tingkat Kerusakan")
        plt.title(f"Hasil Deteksi Serangan Penyakit {penyakit.title()}", fontsize=14)
        with rio.open(input_folder) as src:
            data = src.read(1) 
            plt.imshow(data, cmap=cmaps, norm=norms) 
            plt.show() 
            # plt.savefig(os.path.join(output_folder, f"sebaran_{penyakit}.png"))
        return None

    # Fungsi untuk menghitung sebaran penyakit per rumpun
    def hitung_sebaran_rumpun(self, input_folder):
        """
        Menghitung sebaran penyakit.
        
        Parameters:
            input_folder (str): Lokasi file GeoTIFF hasil prediksi model.
            penyakit (str): Nama penyakit.

        Returns:
            None.
        """
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
        # Menghitung persentase
        persen = {i: round((counts.get(i, 0) / jml_data_valid) * 100, 2) for i in range(1, 5)}
        # Mencetak hasil
        labels = ["sehat", "ringan", "sedang", "parah"]
        for i, label in enumerate(labels, 1):
            print(f"Persentase tanaman {label}: {persen[i]}%")
        #Mengambil nilai persentase untuk logika
        p_sehat = persen[1]
        p_ringan = persen[2]
        p_sedang = persen[3]
        p_parah = persen[4]
        p_parah_total = p_sedang + p_parah # Gabungan sedang dan parah
        # Logika Rekomendasi
        print("-" * 30)
        if p_parah_total > p_sehat or p_parah_total > p_ringan:
            recom = "Tingkat keparahan tinggi, segera lakukan tindakan pengendalian!"
            print(f"Rekomendasi: {recom}")
        elif p_ringan > p_sehat:  
            recom = "Lakukan pemantauan rutin dan tindakan pencegahan."  
            print(f"Rekomendasi: {recom}")
        else:
            recom = "Kondisi Aman: Vegetasi mayoritas dalam keadaan sehat."
            print(f"{recom}")

        persen["rekomendasi"] = recom
        return persen


class PlotDiseaseAnalyzer:
    """
    Kelas untuk memunculkan hasil analisis per plot/petak.
    """ 
    def __init__(self):
        self.status = "Idle"
        self.last_result = None

    def run(self, shp_path, penyakit, output_folder):
        self.status = "Processing"
        print(f"\nDEBUG: Menghitung sebaran dan memunculkan hasil...") 
        try:
            self.tampilkan_penyakit_petak(shp_path, penyakit, output_folder)
            self.last_result = self.hitung_sebaran_petak(shp_path, penyakit) 
            self.status = "Done"
            return self.last_result
        except Exception as e:
            self.status = "Error"
            print(f"\nERROR: {e}")
            return None 
        
    # Fungsi menampilkan hasil prediksi model per petak 
    def tampilkan_penyakit_petak(self, shp_path, penyakit, output_folder):
        """
        Menampilkan peta sebaran pada grafik.
        
        Parameters:
            shp_path (str): Lokasi shapefile hasil prediksi model.
            penyakit (str): Nama penyakit.
            output_folder (str): Nama folder tempat file akan disimpan.

        Returns:
            None.
        """

        print(f"\nMenampilkan peta sebaran penyakit {penyakit.title()}...")
        os.makedirs(output_folder, exist_ok=True)
        alpha = "#00000000"
        hg = "#008000ff"
        ht = "#90ee90ff"
        kuning = "#ffff74ff"
        merah = "#d7191cff"
        warna = [alpha, hg, ht, kuning, merah]
        cmaps = mcolor.ListedColormap(warna)

        bounds = np.arange(-0.5, 5, 1)
        norms = mcolor.BoundaryNorm(bounds, 5)

        gdf = gpd.read_file(shp_path)
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))

        gdf.plot(
            column=penyakit,  
            cmap=cmaps, 
            norm=norms,
            ax=ax,
            edgecolor='black', 
            linewidth=0.3
            )
        
        patches = [
            mpatch.Patch(color=hg, label="Sehat", ec="black"),
            mpatch.Patch(color=ht, label="Ringan", ec="black"),
            mpatch.Patch(color=kuning, label="Sedang", ec="black"),
            mpatch.Patch(color=merah, label="Parah", ec="black")
        ]
        ax.legend(handles=patches, loc="lower right", bbox_to_anchor=(1, 1), title="Tingkat Kerusakan")
        plt.title(f"Hasil Deteksi Serangan Penyakit {penyakit.title()}", fontsize=14)
        plt.show()
        # plt.savefig(os.path.join(output_folder, f"sebaran_petak_{penyakit}.png"))
        return None
        
    # Fungsi untuk menghitung sebaran penyakit per petak
    def hitung_sebaran_petak(self, shp_path, penyakit):
        """
        Menghitung sebaran penyakit.
        
        Parameters:
            shp_path (str): Lokasi shapefile hasil prediksi model.
            penyakit (str): Nama penyakit.

        Returns:
            dict: Hasil analisis.
        """
        print(f"\nMenghitung sebaran penyakit {penyakit.title()}...")
        gdf = gpd.read_file(shp_path)
        data = gdf[penyakit]

        # Menghitung jumlah data
        jml_data = np.count_nonzero(data)
        # Mengambil semua nilai unik
        counts = data.value_counts()

        # Mencetak hasil
        labels = ["sehat", "ringan", "sedang", "parah"]
        persen = {}
        for i, label in enumerate(labels, 1):
            jumlah_spesifik = counts.get(i, 0)
            hasil_persen = round((jumlah_spesifik / jml_data) * 100, 2)
            persen[i] = hasil_persen
            print(f"Persentase tanaman {label}: {persen[i]}%")
        #Mengambil nilai persentase untuk logika
        p_sehat = persen[1]
        p_ringan = persen[2]
        p_sedang = persen[3]
        p_parah = persen[4]
        p_parah_total = p_sedang + p_parah # Gabungan sedang dan parah
        # Logika Rekomendasi
        print("-" * 30)
        if p_parah_total > p_sehat or p_parah_total > p_ringan:
            recom = "Tingkat keparahan tinggi, segera lakukan tindakan pengendalian!"
            print(f"Rekomendasi: {recom}")
        elif p_ringan > p_sehat:  
            recom = "Lakukan pemantauan rutin dan tindakan pencegahan."  
            print(f"Rekomendasi: {recom}")
        else:
            recom = "Kondisi Aman: Vegetasi mayoritas dalam keadaan sehat."
            print(f"{recom}")

        persen["rekomendasi"] = recom
        return persen
    

if __name__ == "__main__":
    geotiff_file = r"C:\Users\acer_\Documents\laporan skrpsi\Pengujian\Hasil\Lahan Uji_Files\Klip\Lahan Uji_clip.tif"
    koords_verteks = r"C:\Users\acer_\Documents\laporan skrpsi\Pengujian\Hasil\Lahan Uji_Files\Koordinat Vertek"
    hasil_prediksi = r"C:\Users\acer_\Documents\laporan skrpsi\Pengujian\Hasil\Lahan Uji_Files\Deteksi\Hasil_Prediksi.xlsx"
    folder_hasil = r"C:\Users\acer_\Documents\laporan skrpsi\Pengujian\Hasil\Lahan Uji_Files\Deteksi" 
    buat_petak_sebaran(geotiff_file, hasil_prediksi, koords_verteks, folder_hasil)