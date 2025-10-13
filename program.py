import ekstraksi
import transformasi

import numpy as np
import pandas as pd
import rasterio as rio
import glob
import os
import matplotlib.pyplot as plt
from mahotas.polygon import fill_polygon
import time

# Fungsi untuk memeriksa ukuran raster
def cek_ukuran_raster(input_raster):
    with rio.open(input_raster) as src:
        print(f"Memeriksa bentuk...")
        band1 = src.read(1)
        print(f"Bentuk (shape) dari {input_raster} adalah {band1.shape}")


# Fungsi untuk menyimpan array NumPy ke dalam file GeoTIFF
def simpan_raster(array_data, profile, output_folder, output_nama_file, nodata_value=None):
    """
    Menyimpan array NumPy sebagai file GeoTIFF ke folder yang ditentukan.

    Args:
        array_data (np.ndarray): Array NumPy yang akan disimpan.
        profile (dict): Metadata raster dari file sumber.
        output_folder (str): Nama folder tempat file akan disimpan.
        output_nama_file (str): Nama file output, termasuk ekstensi.
        
    Returns:
        str: Output path.
    """
    # Gabungkan nama folder dan nama file
    output_path = os.path.join(output_folder, output_nama_file)

    # Pastikan folder output ada, jika tidak, buat folder baru
    os.makedirs(output_folder, exist_ok=True)

    # Perbarui profil untuk file output
    profile.update(
        dtype=array_data.dtype,  
        count=1,
        driver='GTiff'
    )
    if nodata_value is not None:
        profile.update(nodata=nodata_value)
        
    # Tulis array ke file GeoTIFF
    with rio.open(output_path, 'w', **profile) as dst:
        dst.write(array_data, 1)

    print(f"File {output_nama_file} berhasil disimpan di {output_folder}")
    return output_path

# Fungsi untuk menentukan threshold secara otomatis
def otsu_threshold(input_raster, jumlah_bin=256, rentang_nilai=(-1, 1)):
    """
    Menghitung threshold untuk masking raster.

    Args:
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

# Fungsi untuk membuat polygon sebagai grid titik
def render(poly):
    """
    Membuat grid titik dari poligon berdasarkan koordinat piksel.
    Mengembalikan daftar semua koordinat piksel (row, col) di dalam poligon.
    """
    xs, ys = zip(*poly)
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    newPoly = [(int(x - minx), int(y - miny)) for (x, y) in poly]
    grid = np.zeros((maxx - minx + 1, maxy - miny + 1), dtype=np.int8)
    fill_polygon(newPoly, grid)
    return [(x + minx, y + miny) for (x, y) in zip(*np.nonzero(grid))]




########################################################
#
#            PROGRAM UTAMA
#
##########################################################
t0 = time.perf_counter()
# ---- MENENTUKAN FOLDER KERJA ----
# Menentukan lokasi folder, file, dan shapefile yang digunakan
# Memeriksa folder atau file yang akan diproses
try:
    lokasi_folder_raster = input("Masukkan path folder berisi file .tif: ")
    lokasi_folder_shp = input("Masukkan path folder berisi file .shp: ")

    # Cek apakah folder ada
    if not os.path.isdir(lokasi_folder_raster):
        raise FileNotFoundError(f"Folder raster tidak ditemukan: {lokasi_folder_raster}. Silahkan cek dulu")
    if not os.path.isdir(lokasi_folder_shp):
        raise FileNotFoundError(f"Folder shapefile tidak ditemukan: {lokasi_folder_shp}. Silahkan cek dulu")

    # Ambil semua file .tif dan .shp
    file_raster = os.path.join(lokasi_folder_raster, "*.tif")
    file_shp = os.path.join(lokasi_folder_shp, "*.shp")

    raster_input = glob.glob(file_raster)
    shp_input = glob.glob(file_shp)

    # Cek apakah file di dalam folder ditemukan
    if not raster_input:
        print("Tidak ada file .tif ditemukan di folder tersebut.")
    if not shp_input:
        print("Tidak ada file .shp ditemukan di folder tersebut.")

except FileNotFoundError as e:
    print(e)

# Menampilkan file .tif dalam folder 
print(f"Daftar File '.tif' dalam Folder {lokasi_folder_raster}")
c1 = c2 = 1
for raster in raster_input:
    print(f"\t {c1}) {raster}")
    c1 += 1
# Menentukan file .tif yang diproses berdasarkan input pengguna
raster_idx = int(input(f"Pilih file .tif (1-{len(raster_input)}): "))
raster_target = raster_input[raster_idx - 1]
nf_raster = os.path.splitext(os.path.basename(raster_target))[0]
print(f"Memproses {raster_target}...")
# Menampilkan file .shp dalam folder
print(f"Daftar File '.shp' dalam Folder {lokasi_folder_shp}")
for shp in shp_input:
    print(f"\t {c2}) {shp}")
    c2 += 1
# Menentukan file .shp yang diproses berdasarkan input pengguna
print("Silahkan pilih file .shp untuk clipping")
shp_idx = int(input(f"Pilih file .shp (1-{len(shp_input)}): "))
shp_target = shp_input[shp_idx - 1]
print(f"Memproses {shp_target}...")


# ---- PROSES CLIPPING AWAL ----
# ---- MENGAMBIL PETAKAN SAWAH BERDASARKAN POLIGON ----
clipped_file_path = ekstraksi.clip_raster_by_mask(raster_target, shp_target, rf"{lokasi_folder_raster}\Hasil\Clip", f"{nf_raster}_clip.tif")
# Mengakses citra beserta band yang diperlukan 
print("Membaca band yang diperlukan...")
with rio.open(clipped_file_path) as src_citra:
    # Membaca data setiap band
    red = src_citra.read(1)
    green = src_citra.read(2)
    blue = src_citra.read(3)
    m_green = src_citra.read(4)
    m_red = src_citra.read(5)
    red_edge = src_citra.read(6)
    nir = src_citra.read(7)
    # Membaca mask yang berisi data
    valid_mask = src_citra.read_masks(1) > 0
    # Membuat metadata profile
    profile = src_citra.profile


# ---- PROSES SEGMENTASI ----
# ---- Menghitung SAVI ----
# Mentransformasi citra menggunakan SAVI
print("Menghitung SAVI untuk thresholding...")
transform_savi_thresholding = transformasi.hitung_savi(nir, m_red, L=0.5)
# ---- Membaca SAVI dan menampilkan histogram ----
# Mengubah bagian yang bukan data menjadi NaN
transform_savi_thresholding[~valid_mask] = np.nan
# Mengubah array 2D menjadi 1D agar mudah diplot
savi_1d = transform_savi_thresholding[~np.isnan(transform_savi_thresholding)] # Ambil nilai yang bukan NaN
# Membuat histogram untuk menampilkan data piksel SAVI
print("Menampilkan histogram...")
plt.figure(figsize=(10, 6))
plt.hist(savi_1d, bins=100, color='lightgreen', edgecolor='black')
plt.title('Histogram Nilai SAVI')
plt.xlabel('Nilai SAVI')
plt.ylabel('Frekuensi Piksel')
plt.grid(True, alpha=0.5)
# Menggunakan bantuan garis vertikal untuk threshold
plt.axvline(x=0.2, color='r', linestyle='--', label='Contoh Threshold = 0.2')
plt.legend()
plt.show()
# Menyimpan hasil transformasi ke dalam file GeoTIFF
savi_file_path = simpan_raster(transform_savi_thresholding, profile, rf"{lokasi_folder_raster}\Hasil\Thresholding", f"{nf_raster} SAVI.tif")

# ---- Melakukan thresholding ----
print("Memuat file SAVI...")
with rio.open(savi_file_path) as src_savi:
    savi = src_savi.read(1)
# Menentukan threshold vegetasi
opsi_thresholding = input("Tentukan sendiri nilai threshold? (y/n): ")
if opsi_thresholding == "y":
    manual_threshold = float(input("Masukkan nilai threshold: "))
    thresholding = savi > manual_threshold
    print(f"Melakukan thresholding dengan batas {manual_threshold}...")
else :
    auto_threshold = otsu_threshold(savi, jumlah_bin=256, rentang_nilai=(-1, 1))
    thresholding = savi > auto_threshold
    print(f"Melakukan thresholding dengan batas {auto_threshold}...")
hasil_threshold = thresholding.astype(rio.uint8)
# Menyimpan hasil threshold
threshold_file_path = simpan_raster(hasil_threshold, profile, rf"{lokasi_folder_raster}\Hasil\Thresholding", f"{nf_raster} threshold.tif")

# ---- Melakukan masking ----
# Masking kanal green, red, red_edge, dan nir
print("Memuat file threshold...")
with rio.open(threshold_file_path) as src_mask:
    threshold_mask = src_mask.read(1)
masking_vegetasi = (threshold_mask == 1)
# Menerapkan mask
print("Melakukan masking...")
hasil_masking_red = ekstraksi.mask_raster(red, masking_vegetasi, nodata_value=-9999)
hasil_masking_green = ekstraksi.mask_raster(green, masking_vegetasi, nodata_value=-9999)
hasil_masking_blue = ekstraksi.mask_raster(blue, masking_vegetasi, nodata_value=-9999)
hasil_masking_m_green = ekstraksi.mask_raster(m_green, masking_vegetasi, nodata_value=-9999)
hasil_masking_m_red = ekstraksi.mask_raster(m_red, masking_vegetasi, nodata_value=-9999)
hasil_masking_red_edge = ekstraksi.mask_raster(red_edge, masking_vegetasi, nodata_value=-9999)
hasil_masking_nir = ekstraksi.mask_raster(nir, masking_vegetasi, nodata_value=-9999)
# Menyimpan raster hasil masking
red_mask_path = simpan_raster(hasil_masking_red, profile, rf"{lokasi_folder_raster}\Hasil\Masking dan Transformasi", f"{nf_raster} RED.tif", nodata_value=-9999)
green_mask_path = simpan_raster(hasil_masking_green, profile, rf"{lokasi_folder_raster}\Hasil\Masking dan Transformasi", f"{nf_raster} GREEN.tif", nodata_value=-9999)
blue_mask_path = simpan_raster(hasil_masking_blue, profile, rf"{lokasi_folder_raster}\Hasil\Masking dan Transformasi", f"{nf_raster} BLUE.tif", nodata_value=-9999)
m_green_mask_path = simpan_raster(hasil_masking_m_green, profile, rf"{lokasi_folder_raster}\Hasil\Masking dan Transformasi", f"{nf_raster} M_GREEN.tif", nodata_value=-9999)
m_red_mask_path = simpan_raster(hasil_masking_m_red, profile, rf"{lokasi_folder_raster}\Hasil\Masking dan Transformasi", f"{nf_raster} M_RED.tif", nodata_value=-9999)
red_edge_mask_path = simpan_raster(hasil_masking_red_edge, profile, rf"{lokasi_folder_raster}\Hasil\Masking dan Transformasi", f"{nf_raster} RED_EDGE.tif", nodata_value=-9999)
nir_mask_path = simpan_raster(hasil_masking_nir, profile, rf"{lokasi_folder_raster}\Hasil\Masking dan Transformasi", f"{nf_raster} NIR.tif", nodata_value=-9999)


# ---- PROSES TRANSFORMASI ----
# --- Menghitung NDVI ----
# Memuat Band NIR dan Red hasil masking
print("Memuat file mask...")
with rio.open(m_green_mask_path) as src_m_green_mask, rio.open(m_red_mask_path) as src_m_red_mask, rio.open(red_edge_mask_path) as src_red_edge_mask, rio.open(nir_mask_path) as src_nir_mask :
    m_green_masked = src_m_green_mask.read(1)
    m_red_masked = src_m_red_mask.read(1)
    red_edge_masked = src_red_edge_mask.read(1)
    nir_masked = src_nir_mask.read(1)
# Mentransformasi citra menggunakan NDVI
print("Menghitung NDVI...")
transform_ndvi = transformasi.hitung_ndvi(nir_masked, m_red_masked)
transform_ndvi[(nir_masked == -9999) | (m_red_masked == -9999)] = -9999
# Menyimpan hasil transformasi
ndvi_file_path = simpan_raster(transform_ndvi, profile, rf"{lokasi_folder_raster}\Hasil\Masking dan Transformasi", f"{nf_raster} NDVI.tif")
# Mentransformasi citra menggunakan GNDVI
print("Menghitung GNDVI...")
transform_gndvi = transformasi.hitung_gndvi(nir_masked, m_green_masked)
transform_ndvi[(nir_masked == -9999) | (m_green_masked == -9999)] = -9999
# Menyimpan hasil transformasi
gndvi_file_path = simpan_raster(transform_ndvi, profile, rf"{lokasi_folder_raster}\Hasil\Masking dan Transformasi", f"{nf_raster} GNDVI.tif")
# Mentransformasi citra menggunakan NDREI
print("Menghitung NDREI...")
transform_ndrei = transformasi.hitung_ndrei(nir_masked, red_edge_masked)
transform_ndrei[(nir_masked == -9999) | (red_edge_masked == -9999)] = -9999
# Menyimpan hasil transformasi
ndrei_file_path = simpan_raster(transform_ndrei, profile, rf"{lokasi_folder_raster}\Hasil\Masking dan Transformasi", f"{nf_raster} NDREI.tif")
# Mentransformasi citra menggunakan SAVI
print("Menghitung SAVI...")
transform_savi = transformasi.hitung_savi(nir_masked, m_red_masked, L=0.5)
transform_savi[(nir_masked == -9999) | (m_red_masked == -9999)] = -9999
# Menyimpan hasil transformasi
savi_file_path = simpan_raster(transform_savi, profile, rf"{lokasi_folder_raster}\Hasil\Masking dan Transformasi", f"{nf_raster} SAVI.tif")

# ---- PROSES EKSTRAKSI ----
# --- Menentukan lokasi file ----
csv_path = input("Masukkan path file verteks poligon (.csv): ")  # File verteks poligon
folder_ekstraksi = rf"{lokasi_folder_raster}\Hasil\Masking dan Transformasi" # Folder tempat citra akan diekstrak
file_ekstraksi = glob.glob(os.path.join(folder_ekstraksi, "*tif"))  # File .tif yang ingin dibaca
# --- Membaca file verteks ----
df = pd.read_csv(csv_path)
grup = df.groupby("id")
hasil_gabungan_band = None # Data gabungan semua band yang diekstrak
# --- Memproses setiap file dalam folder ----
for file in file_ekstraksi:
    nf_ekstraksi = os.path.splitext(os.path.basename(file))[0] # Nama file yang diekstrak
    nama_band = nf_ekstraksi.split(" ")[-1] # Nama band file yang diekstrak
    print(f"Mengekstrak piksel: {nama_band}...")
    # --- Membaca raster ----
    with rio.open(file) as src:
        band_data = src.read(1)
        transform = src.transform
        nilai_nodata = src.nodata

    hasil_ekstraksi = []

    # --- Memproses setiap poligon berdasarkan ID ----
    for id_petak, data in grup:
        nama_poli = data["nama"].iloc[0]
        xs, ys = data["X"].to_numpy(), data["Y"].to_numpy()
        # Konversi koordinat UTM ke baris dan kolom raster
        rows, cols = rio.transform.rowcol(transform, xs, ys)
        vertek = list(zip(rows, cols))
        # Menentukan semua piksel di dalam poligon
        x1, y1 = zip(*render(vertek))
        # Mengambil nilai piksel dan konversi ke koordinat spasial
        for (r, c) in zip(x1, y1):
            nilai_piksel = band_data[r, c]
            X, Y = rio.transform.xy(transform, r, c)
            # Lewati nilai piksel nodata
            if nilai_piksel == nilai_nodata:
                continue

            hasil_ekstraksi.append({
                "id": id_petak,
                "nama": nama_poli,
                "row": r,
                "col": c,
                "X": X,
                "Y": Y,
                nama_band: nilai_piksel
            })

    df_band = pd.DataFrame(hasil_ekstraksi)
    # Menggabungkan hasil ekstraksi 
    if hasil_gabungan_band is None:
        hasil_gabungan_band = df_band
    else: 
        hasil_gabungan_band = pd.merge(
            hasil_gabungan_band, 
            df_band,
            on=["id", "nama", "row", "col", "X", "Y"],
            how="outer"
        )

# --- Menyimpan hasil ekstraksi ke CSV ----
nf_hasil = f"Hasil_Ekstraksi_{nf_raster}.csv"
# Pastikan folder output ada
os.makedirs(rf"{lokasi_folder_raster}\Hasil\Ekstraksi", exist_ok=True)
path_hasil_ekstraksi = os.path.join(rf"{lokasi_folder_raster}\Hasil\Ekstraksi", nf_hasil)
urutan_band = ["RED", "GREEN", "BLUE", "M_GREEN", "M_RED", "RED_EDGE", "NIR", "SAVI", "NDVI", "GNDVI", "NDREI"]
kolom_awal = ["id", "nama", "row", "col", "X", "Y"]
kolom_akhir = kolom_awal + [b for b in urutan_band if b in hasil_gabungan_band.columns]
hasil_gabungan_band = hasil_gabungan_band[kolom_akhir]
# Simpan hasil ekstraksi ke csv
hasil_gabungan_band.to_csv(path_hasil_ekstraksi, index=False)
print(f"Ekstraksi selesai.")
print(rf"File {nf_hasil} berhasil disimpan di {lokasi_folder_raster}\Hasil\Ekstraksi")


# ---- PROSES TAMBAHAN ----
# --- Menghitung ukuran raster ----
# cek_ukuran_raster(raster_target)
# cek_ukuran_raster(clipped_file_path)
# cek_ukuran_raster(savi_file_path)
# cek_ukuran_raster(threshold_file_path)
# cek_ukuran_raster(m_green_mask_path)
# cek_ukuran_raster(m_red_mask_path)
# cek_ukuran_raster(red_edge_mask_path)
# cek_ukuran_raster(nir_mask_path)
# cek_ukuran_raster(ndvi_file_path)
print('aman aja')

t1 = time.perf_counter()
t = t1 - t0
print(f"\nSelesai dalam {t: 3.2f} detik")
    