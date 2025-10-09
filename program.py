import ekstraksi
import transformasi

import numpy as np
import rasterio
import glob
import os
import matplotlib.pyplot as plt

# Fungsi untuk memeriksa ukuran raster
def cek_ukuran_raster(input_raster):
    with rasterio.open(input_raster) as src:
        print(f"Memeriksa bentuk...")
        band1 = src.read(1)
        print(f"Bentuk (shape) dari {input_raster} adalah {band1.shape}")


# Fungsi untuk menyimpan array NumPy ke dalam file GeoTIFF
def simpan_raster(array_data, profile, output_folder, output_filename, nodata_value=None):
    """
    Menyimpan array NumPy sebagai file GeoTIFF ke folder yang ditentukan.

    Args:
        array_data (np.ndarray): Array NumPy yang akan disimpan.
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
        dtype=array_data.dtype,  
        count=1,
        driver='GTiff'
    )
    if nodata_value is not None:
        profile.update(nodata=nodata_value)
        
    # Tulis array ke file GeoTIFF
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(array_data, 1)

    print(f"File {output_filename} berhasil disimpan di {output_folder}")
    return output_path

# Fungsi untuk menentukan threshold secara otomatis
import numpy as np

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


# ---- Menetukan folder kerja ----
# Menentukan lokasi folder, file, dan shapefile yang digunakan
folder_input_path = r"Bahan/*.tif"
file_input = glob.glob(folder_input_path)
shp_input_path = r"Shapefiles/*.shp"
shp_input = glob.glob(shp_input_path)
nama_proyek = input("Silahkan masukkan nama proyek: ")
# Memeriksa file yang relevan pada folder 
print("Memeriksa folder...")
print("Daftar File '.tif' dalam Folder Bahan")
c1 = c2 = 1
for i in file_input:
    print(f"\t {c1}) {i}")
    c1 += 1
# Menentukan file .tif yang diproses berdasarkan input pengguna
file_target = int(input(f"Pilih file .tif (1-{len(file_input)}): "))
print(f"Memproses {file_input[file_target - 1]}...")
print("Daftar File '.shp' dalam Folder Shapefiles")
for i in shp_input:
    print(f"\t {c2}) {i}")
    c2 += 1
# Menentukan file .shp yang diproses berdasarkan input pengguna
print("Silahkan pilih file .shp untuk clipping")
shp_target = int(input(f"Pilih file .shp (1-{len(shp_input)}): "))
print(f"Memproses {shp_input[shp_target - 1]}...")

# ---- Mengakses citra multispektral ---- 
# ---- Mengambil petakan sawah berdasarkan shapefile poligon ----
clipped_file_path = ekstraksi.clip_raster_by_mask(file_input[file_target - 1], shp_input[shp_target - 1], f"{nama_proyek}_clip.tif")
# Mengakses citra beserta band yang diperlukan 
print("Membaca band yang diperlukan...")
with rasterio.open(clipped_file_path) as src_citra:
    # Membaca data setiap band
    green = src_citra.read(4)
    red = src_citra.read(5)
    red_edge = src_citra.read(6)
    nir = src_citra.read(7)
    # Membaca mask yang berisi data
    valid_mask = src_citra.read_masks(1) > 0
    # Membuat metadata profile
    profile = src_citra.profile

# ---- Menghitung SAVI ----
# Mentransformasi citra menggunakan SAVI
print("Menghitung SAVI...")
transform_savi = transformasi.hitung_savi(nir, red, L=0.5)
# ---- Membaca SAVI dan menampilkan histogram ----
# Mengubah bagian yang bukan data menjadi NaN
transform_savi[~valid_mask] = np.nan
# Mengubah array 2D menjadi 1D agar mudah diplot
savi_1d = transform_savi[~np.isnan(transform_savi)] # Ambil nilai yang bukan NaN
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
savi_file_path = simpan_raster(transform_savi, profile, "Hasil/Transformasi/SAVI", f"{nama_proyek}_SAVI.tif")

# ---- Melakukan thresholding ----
print("Memuat file SAVI...")
with rasterio.open(savi_file_path) as src_savi:
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
hasil_threshold = thresholding.astype(rasterio.uint8)
# Menyimpan hasil threshold
threshold_file_path = simpan_raster(hasil_threshold, profile, "Hasil/Threshold", f"{nama_proyek}_threshold.tif")

# ---- Melakukan masking ----
# Masking kanal green, red, red_edge, dan nir
print("Memuat file threshold...")
with rasterio.open(threshold_file_path) as src_mask:
    threshold_mask = src_mask.read(1)
masking_vegetasi = (threshold_mask == 1)
# Menerapkan mask
print("Melakukan masking...")
hasil_masking_green = ekstraksi.mask_raster(green, masking_vegetasi, nodata_value=-9999)
hasil_masking_red = ekstraksi.mask_raster(red, masking_vegetasi, nodata_value=-9999)
hasil_masking_red_edge = ekstraksi.mask_raster(red_edge, masking_vegetasi, nodata_value=-9999)
hasil_masking_nir = ekstraksi.mask_raster(nir, masking_vegetasi, nodata_value=-9999)
# Menyimpan raster hasil masking
green_mask_path = simpan_raster(hasil_masking_green, profile, "Hasil/Mask", f"{nama_proyek}_green.tif", nodata_value=-9999)
red_mask_path = simpan_raster(hasil_masking_red, profile, "Hasil/Mask", f"{nama_proyek}_red.tif", nodata_value=-9999)
red_edge_mask_path = simpan_raster(hasil_masking_red_edge, profile, "Hasil/Mask", f"{nama_proyek}_red_edge.tif", nodata_value=-9999)
nir_mask_path = simpan_raster(hasil_masking_nir, profile, "Hasil/Mask", f"{nama_proyek}_nir.tif", nodata_value=-9999)

# --- Menghitung NDVI ----
# Memuat Band NIR dan Red hasil masking
print("Memuat file mask...")
with rasterio.open(nir_mask_path) as src_nir_mask, rasterio.open(red_mask_path) as src_red_mask:
    nir_masked = src_nir_mask.read(1)
    red_masked = src_red_mask.read(1)
# Mentransformasi citra menggunakan NDVI
print("Menghitung NDVI...")
transform_ndvi = transformasi.hitung_ndvi(nir_masked, red_masked)
transform_ndvi[(nir_masked == -9999) | (red_masked == -9999)] = -9999
# Menyimpan hasil transformasi ke dalam file GeoTIFF
ndvi_file_path = simpan_raster(transform_ndvi, profile, "Hasil/Transformasi/NDVI", f"{nama_proyek}_NDVI.tif")
cek_ukuran_raster(file_input[file_target - 1])
cek_ukuran_raster(clipped_file_path)
cek_ukuran_raster(savi_file_path)
cek_ukuran_raster(threshold_file_path)
cek_ukuran_raster(green_mask_path)
cek_ukuran_raster(red_mask_path)
cek_ukuran_raster(red_edge_mask_path)
cek_ukuran_raster(nir_mask_path)
cek_ukuran_raster(ndvi_file_path)
print('aman aja')
    