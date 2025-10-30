import ekstraksi
import transformasi
from segmentasi_gulma import pisahkan_gulma

import numpy as np
import pandas as pd
import rasterio as rio
import glob
import os
import matplotlib.pyplot as plt
import time
from tqdm import tqdm

# Fungsi untuk meminta folder path
def ambil_file(ekstensi):
    """
    Mengambil file dengan ekstensi tertentu
    dalam suatu folder berdasarkan input.

    Args:
        ekstensi (str): Ekstensi file yang diambil.

    Returns:
        list: File target dan lokasi folder
    """
    while True:
        lokasi_folder = input(f"\nMasukkan path folder berisi file .{ekstensi}: ").strip('"').strip("'")
        if  not os.path.isdir(lokasi_folder):
            print(f"Folder tidak ditemukan: {lokasi_folder}")
            print("Silahkan dicek dahulu.")
            continue
        folder_target = os.path.join(lokasi_folder, f"*.{ekstensi}")
        file_target = glob.glob(folder_target)
        if not file_target:
            print(f"Tidak ada file .{ekstensi} ditemukan di folder tersebut.")
            print("Silahkan dicek dahulu.")
        else:
            print(f"Ditemukan {len(file_target)} file .{ekstensi} di folder {lokasi_folder}")
            # Menampilkan file dalam folder 
            print(f"Daftar File '.{ekstensi}' dalam Folder {lokasi_folder}")
            c = 1
            for files in file_target:
                print(f"\t {c}) {files}")
                c += 1
            return file_target, lokasi_folder

# Fungsi untuk memeriksa ukuran raster
def cek_ukuran_raster(input_raster):
    """
    Menghitung ukuran raster dan menampilkannya di terminal/shell.

    Args:
        input_raster (np.ndarray): Array NumPy yang akan dihitung.
        
    Returns:
        None.
    """
    with rio.open(input_raster) as src:
        print(f"Memeriksa bentuk...")
        band1 = src.read(1)
        print(f"Bentuk (shape) dari {input_raster} adalah {band1.shape}")

# Fungsi untuk menyimpan array NumPy ke dalam file GeoTIFF
def simpan_raster(input_raster, profile, output_folder, output_nama_file, nodata_value=None):
    """
    Menyimpan array NumPy sebagai file GeoTIFF ke folder yang ditentukan.

    Args:
        input_raster (np.ndarray): Array NumPy yang akan disimpan.
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
        dtype=input_raster.dtype,  
        count=1,
        driver='GTiff'
    )
    if nodata_value is not None:
        profile.update(nodata=nodata_value)
        
    # Tulis array ke file GeoTIFF
    with rio.open(output_path, 'w', **profile) as dst:
        dst.write(input_raster, 1)

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

# Fungsi menampilkan histogram 
def tampilkan_histogram(nama, data, threshold):
    """
    Menampilkan histogram dari hasil perhitungan transformasi indeks vegetasi.

    Args:
        nama (str): Nama transformasi indeks vegetasi yang digunakan.
        data (np.ndarray): Array NumPy yang akan ditampilkan.
        threshold (float): Batas yang ditentukan.
        
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
    # Menggunakan bantuan garis vertikal untuk threshold
    plt.axvline(x=threshold, color='r', linestyle='--', label=f'Threshold = {threshold}')
    plt.legend()
    plt.show()

# Fungsi menumpuk semua fitur (band)
def tumpuk_fitur(list_fitur, output_folder):
    """
    Menumpuk seluruh band atau fitur menjadi array tiga dimensi.

    Args:
        list_fitur (list): List fitur-fitur yang akan ditumpuk.
        output_folder (str): Nama folder tempat file akan disimpan.
        
    Returns:
        str: Output path.
    """
    # Baca semua file dan kumpulkan datanya
    feature_stack = []
    profile = None # Kita akan ambil metadata dari file pertama

    for fitur in list_fitur:
        with rio.open(fitur) as src:
            if profile is None:
                profile = src.profile
            
            # Baca semua band dari file ini
            feature_stack.append(src.read())

    # Gabungkan semua data menjadi satu array NumPy besar
    full_stack_array = np.vstack(feature_stack)

    # Perbarui profile untuk file stack baru
    total_bands = full_stack_array.shape[0]
    profile.update(count=total_bands, nodata=np.nan) 

    # Tulis ke file stack baru
    with rio.open(output_folder, 'w', **profile) as dst:
        dst.write(full_stack_array)

    print(f"Selesai! Tumpukan fitur dengan {total_bands} band disimpan di: {output_folder}")
    return output_folder

########################################################
#
#            PROGRAM UTAMA
#
##########################################################
t0 = time.perf_counter()
# ---- MENENTUKAN FOLDER KERJA ----
raster_input, lokasi_folder_raster = ambil_file("tif")
# Menentukan file .tif yang diproses berdasarkan input pengguna
raster_idx = int(input(f"Pilih file .tif: "))
raster_target = raster_input[raster_idx - 1]
nf_raster = os.path.splitext(os.path.basename(raster_target))[0]
print(f"Memproses {raster_target}...")
# Menentukan file .shp yang diproses berdasarkan input pengguna
shp_input, lokasi_folder_shp = ambil_file("shp")
shp_idx = int(input(f"Pilih file .shp untuk clipping: "))
shp_target = shp_input[shp_idx - 1]
print(f"Memproses {shp_target}...")

# ---- PROSES CLIPPING AWAL ----
# ---- MENGAMBIL PETAKAN SAWAH BERDASARKAN POLIGON ----
clipped_file_path = ekstraksi.clip_raster(raster_target, shp_target, rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Clip", f"{nf_raster}_clip.tif")
# Mengakses citra beserta band yang diperlukan 
with rio.open(clipped_file_path) as src_citra:
    # Membaca data setiap band
    red = src_citra.read(1)
    green = src_citra.read(2)
    blue = src_citra.read(3)
    m_green = src_citra.read(4)
    m_red = src_citra.read(5)
    red_edge = src_citra.read(6)
    nir = src_citra.read(7)
    nodata_asli = src_citra.nodata
    # Memisahkan bagian yang tidak valid
    mask_citra = src_citra.read_masks(1)
    invalid_mask = (mask_citra == 0)
    # Membuat metadata profile
    profile = src_citra.profile
# Menampilkan mask citra hasil clipping
plt.figure(figsize=(8, 6)) # Tambahkan ini untuk ukuran plot yang lebih baik
plt.title("Tampilan Mask Hasil Clipping")
plt.imshow(mask_citra, cmap='gray') 
plt.show()
print("\nMembaca band yang diperlukan...")

# ---- PROSES SEGMENTASI ----
# ---- Menghitung SAVI ----
# Mentransformasi citra menggunakan SAVI dan NDREI
# Mengeliminasi nodata dari band untuk perhitungan 
nir_valid = np.ma.masked_array(nir, mask=invalid_mask)
m_red_valid = np.ma.masked_array(m_red, mask=invalid_mask)
red_edge_valid = np.ma.masked_array(red_edge, mask=invalid_mask)
m_green_valid = np.ma.masked_array(m_green, mask=invalid_mask)
print("Menghitung SAVI dan NDREI untuk thresholding...")
transform_savi_thresholding = transformasi.hitung_savi(nir_valid, m_red_valid, L=0.5)
transform_ndrei_thresholding = transformasi.hitung_ndrei(nir_valid, red_edge_valid)
transform_ndvi_thresholding = transformasi.hitung_ndvi(nir_valid, m_red_valid)
transform_gndvi_thresholding = transformasi.hitung_gndvi(nir_valid, m_green_valid)
# ---- Membaca SAVI dan NDREI lalu menampilkan histogram ----
# Mengubah array 2D menjadi 1D agar mudah diplot
savi_1d = transform_savi_thresholding.ravel() 
ndrei_1d = transform_ndrei_thresholding.ravel()
# Menyimpan hasil transformasi ke dalam file GeoTIFF
savi_file_path = simpan_raster(transform_savi_thresholding, profile, rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Thresholding", "threshold_SAVI.tif", nodata_value=np.nan)
ndrei_file_path = simpan_raster(transform_ndrei_thresholding, profile, rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Thresholding", "threshold_NDREI.tif", nodata_value=np.nan)
ndvi_file_path = simpan_raster(transform_ndvi_thresholding, profile, rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Thresholding", "threshold_NDVI.tif", nodata_value=np.nan)
gndvi_file_path = simpan_raster(transform_gndvi_thresholding, profile, rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Thresholding", "threshold_GNDVI.tif", nodata_value=np.nan)
# ---- Melakukan thresholding ----
# Menumpuk fitur untuk segmentasi gulma
lst_fitur = [
    clipped_file_path,
    gndvi_file_path,
    ndrei_file_path,
    ndvi_file_path,
    savi_file_path
]
lokasi_fitur_stack = tumpuk_fitur(lst_fitur, output_folder=rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Thresholding\tumpukan_fitur.tif")
# Membuat peta segmentasi gulma dan padi
peta_segmentasi_gulma = pisahkan_gulma(model_path="model_random_forest_0.joblib", stack_path=lokasi_fitur_stack, output_folder=rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Thresholding\segmentasi_gulma.tif")
print("Memuat file SAVI...")
with rio.open(savi_file_path) as src_savi, rio.open(peta_segmentasi_gulma) as src_gulma, rio.open(ndrei_file_path) as src_ndrei:
    savi = src_savi.read(1).astype("float32")
    ndrei = src_ndrei.read(1).astype("float32")
    mask_padi = src_gulma.read(1).astype("float32") < 2
    savi_nodata = src_savi.nodata
t_savi = otsu_threshold(savi, jumlah_bin=256, rentang_nilai=(-1, 1))
t_ndrei = -0.05
# Menampilkan histogram SAVI
tampilkan_histogram("SAVI", savi_1d, t_savi)
tampilkan_histogram("NDREI", ndrei_1d, t_ndrei)
mask_savi = savi > t_savi
mask_ndrei = ndrei > t_ndrei
mask_final = mask_savi & mask_padi
mask_final_indeks = mask_savi & mask_ndrei
print(f"Melakukan thresholding SAVI dengan batas {t_savi}...")
hasil_threshold = mask_final.astype("float32")
hasil_threshold_2 = mask_final_indeks.astype("float32")
# Menyimpan hasil threshold
threshold_file_path = simpan_raster(hasil_threshold, profile, rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Thresholding", "hasil_threshold_model.tif", nodata_value=savi_nodata)
threshold2_file_path = simpan_raster(hasil_threshold_2, profile, rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Thresholding", "hasil_threshold_indeks.tif", nodata_value=savi_nodata)
os.remove(lokasi_fitur_stack)
os.remove(gndvi_file_path)
os.remove(ndvi_file_path)

# ---- Melakukan masking ----
# Masking kanal green, red, red_edge, dan nir
print("\nMemuat file threshold...")
with rio.open(threshold_file_path) as src_mask:
    threshold_mask = src_mask.read(1)
masking_vegetasi = (threshold_mask == 1)
# Menerapkan mask
print("Melakukan masking...")
hasil_masking_red = ekstraksi.mask_raster(red, masking_vegetasi, nodata_value=np.nan)
hasil_masking_green = ekstraksi.mask_raster(green, masking_vegetasi, nodata_value=np.nan)
hasil_masking_blue = ekstraksi.mask_raster(blue, masking_vegetasi, nodata_value=np.nan)
hasil_masking_m_green = ekstraksi.mask_raster(m_green, masking_vegetasi, nodata_value=np.nan)
hasil_masking_m_red = ekstraksi.mask_raster(m_red, masking_vegetasi, nodata_value=np.nan)
hasil_masking_red_edge = ekstraksi.mask_raster(red_edge, masking_vegetasi, nodata_value=np.nan)
hasil_masking_nir = ekstraksi.mask_raster(nir, masking_vegetasi, nodata_value=np.nan)
# Menyimpan raster hasil masking
red_mask_path = simpan_raster(hasil_masking_red, profile, rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Masking dan Transformasi", "RED.tif", nodata_value=np.nan)
green_mask_path = simpan_raster(hasil_masking_green, profile, rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Masking dan Transformasi", "GREEN.tif", nodata_value=np.nan)
blue_mask_path = simpan_raster(hasil_masking_blue, profile, rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Masking dan Transformasi", "BLUE.tif", nodata_value=np.nan)
m_green_mask_path = simpan_raster(hasil_masking_m_green, profile, rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Masking dan Transformasi", "M_GREEN.tif", nodata_value=np.nan)
m_red_mask_path = simpan_raster(hasil_masking_m_red, profile, rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Masking dan Transformasi", "M_RED.tif", nodata_value=np.nan)
red_edge_mask_path = simpan_raster(hasil_masking_red_edge, profile, rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Masking dan Transformasi", "RED_EDGE.tif", nodata_value=np.nan)
nir_mask_path = simpan_raster(hasil_masking_nir, profile, rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Masking dan Transformasi", "NIR.tif", nodata_value=np.nan)


# ---- PROSES TRANSFORMASI ----
# --- Menghitung NDVI ----
# Memuat Band NIR dan Red hasil masking
print("\nMemuat file mask...")
with rio.open(m_green_mask_path) as src_m_green_mask, rio.open(m_red_mask_path) as src_m_red_mask, rio.open(red_edge_mask_path) as src_red_edge_mask, rio.open(nir_mask_path) as src_nir_mask :
    m_green_masked = src_m_green_mask.read(1)
    m_red_masked = src_m_red_mask.read(1)
    red_edge_masked = src_red_edge_mask.read(1)
    nir_masked = src_nir_mask.read(1)
# Mentransformasi citra menggunakan NDVI
print("Menghitung NDVI...")
transform_ndvi = transformasi.hitung_ndvi(nir_masked, m_red_masked)
# transform_ndvi[(nir_masked == -9999) | (m_red_masked == -9999)] = -9999
# Menyimpan hasil transformasi
ndvi_file_path = simpan_raster(transform_ndvi, profile, rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Masking dan Transformasi", "NDVI.tif")
# Mentransformasi citra menggunakan GNDVI
print("Menghitung GNDVI...")
transform_gndvi = transformasi.hitung_gndvi(nir_masked, m_green_masked)
# transform_ndvi[(nir_masked == -9999) | (m_green_masked == -9999)] = -9999
# Menyimpan hasil transformasi
gndvi_file_path = simpan_raster(transform_ndvi, profile, rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Masking dan Transformasi", "GNDVI.tif")
# Mentransformasi citra menggunakan NDREI
print("Menghitung NDREI...")
transform_ndrei = transformasi.hitung_ndrei(nir_masked, red_edge_masked)
# transform_ndrei[(nir_masked == -9999) | (red_edge_masked == -9999)] = -9999
# Menyimpan hasil transformasi
ndrei_file_path = simpan_raster(transform_ndrei, profile, rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Masking dan Transformasi", "NDREI.tif")
# Mentransformasi citra menggunakan SAVI
print("Menghitung SAVI...")
transform_savi = transformasi.hitung_savi(nir_masked, m_red_masked, L=0.5)
# transform_savi[(nir_masked == -9999) | (m_red_masked == -9999)] = -9999
# Menyimpan hasil transformasi
savi_file_path = simpan_raster(transform_savi, profile, rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Masking dan Transformasi", "SAVI.tif")

# ---- PROSES EKSTRAKSI ----
# --- Menentukan lokasi file ----
csv_path = input("Path file csv: ")  # File verteks poligon
folder_ekstraksi = rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Masking dan Transformasi" # Folder tempat citra akan diekstrak
file_ekstraksi = glob.glob(os.path.join(folder_ekstraksi, "*tif"))  # File .tif yang ingin dibaca
# --- Membaca file verteks ----
df = pd.read_csv(csv_path)
grup = df.groupby("FID")
hasil_gabungan_band = None # Data gabungan semua band yang diekstrak
# --- Memproses setiap file dalam folder ----
for file in file_ekstraksi:
    nama_band = os.path.splitext(os.path.basename(file))[0] # Nama file yang diekstrak
    # --- Membaca raster ----
    with rio.open(file) as src:
        band_data = src.read(1)
        transform = src.transform
        nilai_nodata = src.nodata

    hasil_ekstraksi = []

    # --- Memproses setiap poligon berdasarkan ID ----
    for id_petak, data in tqdm(grup, desc=f"\nMengkestrak {nama_band}", unit=" petak"):
        nama_poli = data["NAME"].iloc[0]
        xs, ys = data["X"].to_numpy(), data["Y"].to_numpy()
        # Konversi koordinat UTM ke baris dan kolom raster
        rows, cols = rio.transform.rowcol(transform, xs, ys)
        vertek = list(zip(rows, cols))
        # Menentukan semua piksel di dalam poligon
        x1, y1 = zip(*ekstraksi.render(vertek))
        # Mengambil nilai piksel dan konversi ke koordinat spasial
        for (r, c) in zip(x1, y1):
            nilai_piksel = band_data[r, c]
            X, Y = rio.transform.xy(transform, r, c)
            # Lewati nilai piksel nodata
            if nilai_piksel == nilai_nodata:
                continue

            hasil_ekstraksi.append({
                "FID": id_petak,
                "NAME": nama_poli,
                "row": r,
                "col": c,
                "X": X,
                "Y": Y,
                nama_band: nilai_piksel
            })
        
        tqdm.write(f"Poligon {nama_poli} selesai ({len(x1)} piksel)")

    df_band = pd.DataFrame(hasil_ekstraksi)
    # Menggabungkan hasil ekstraksi 
    if hasil_gabungan_band is None:
        hasil_gabungan_band = df_band
    else: 
        hasil_gabungan_band = pd.merge(
            hasil_gabungan_band, 
            df_band,
            on=["FID", "NAME", "row", "col", "X", "Y"],
            how="outer"
        )

# --- Menyimpan hasil ekstraksi ke CSV ----
nf_hasil_ekstraksi = f"Hasil_Ekstraksi_{nf_raster}.csv"
# Pastikan folder output ada
os.makedirs(rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files", exist_ok=True)
path_hasil_ekstraksi = os.path.join(rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files", nf_hasil_ekstraksi)
urutan_band = ["RED", "GREEN", "BLUE", "M_GREEN", "M_RED", "RED_EDGE", "NIR", "SAVI", "NDVI", "GNDVI", "NDREI"]
kolom_awal = ["FID", "NAME", "row", "col", "X", "Y"]
kolom_akhir = kolom_awal + [b for b in urutan_band if b in hasil_gabungan_band.columns]
hasil_gabungan_band = hasil_gabungan_band[kolom_akhir]
# Simpan hasil ekstraksi ke csv
hasil_gabungan_band.to_csv(path_hasil_ekstraksi, index=False)
print(f"Ekstraksi selesai.")
print(rf"File {nf_hasil_ekstraksi} berhasil disimpan di {lokasi_folder_raster}\Hasil\{nf_raster}_Files")


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
if t < 60:
    print(f"\nSelesai dalam {t: 3.2f} detik")
else:
    menit = int(t // 60)
    ts = t % 60
    print(f"\nSelesai dalam {menit:d} menit {ts: 3.2f} detik")
