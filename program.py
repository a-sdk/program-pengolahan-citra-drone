import ekstraksi
import transformasi

import rasterio
import glob
import os
import matplotlib.pyplot as plt

# Fungsi untuk memeriksa ukuran raster
def ukuran_raster(input_raster):
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


# ---- Menetukan folder kerja ----
# Menentukan lokasi folder, file, dan shapefile yang digunakan
folder_input_path = r"Bahan/*.tif"
file_input = glob.glob(folder_input_path)
shp_input_path = r"Shapefiles/*.shp"
shp_input = glob.glob(shp_input_path)
# Memeriksa file yang relevan pada folder input
print("Daftar File '.tif' dalam Folder Input")
for i in file_input:
    print("\t", i)
print("Daftar File '.shp' dalam Folder Shapefiles")
for i in shp_input:
    print("\t", i)
print(f"Memproses {file_input[2]}...")
print(f"Memproses {shp_input[1]}...")

# ---- Mengakses citra multispektral ---- 
# ---- Mengambil petakan sawah berdasarkan shapefile poligon ----
clipped_file_path = ekstraksi.clip_raster_by_mask(file_input[2], shp_input[1])
# Mengakses citra beserta band yang diperlukan 
print("Membaca band yang diperlukan...")
with rasterio.open(clipped_file_path) as citra_src:
    # Membaca data setiap band
    green = citra_src.read(4)
    red = citra_src.read(5)
    red_edge = citra_src.read(6)
    nir = citra_src.read(7)
    # Membuat metadata profile
    profile = citra_src.profile

# ---- Menghitung SAVI ----
# Mentransformasi citra menggunakan SAVI
print("Menghitung SAVI...")
transform_savi = transformasi.hitung_savi(nir, red, L=0.5)
# Menyimpan hasil transformasi ke dalam file GeoTIFF
savi_file_path = simpan_raster(transform_savi, profile, "Hasil/Transformasi/SAVI","SAVI_1_L05.tif")

# ---- Membaca SAVI dan menampilkan histogram ----
# Membaca hasil transformasi SAVI 
print("Membaca SAVI...")
with rasterio.open(savi_file_path) as src_savi:
    # Baca band pertama sebagai numpy array
    savi = src_savi.read(1).astype('float32')
    # Ini akan membuat array di mana True berarti data valid
    boolean_mask = src_savi.read_masks(1) > 0
    # .flatten() mengubah array 2D menjadi 1D agar mudah diplot
    valid_savi = savi[boolean_mask]

# Membuat histogram untuk menampilkan data piksel SAVI
print("Menampilkan histogram...")
plt.figure(figsize=(10, 6))
plt.hist(valid_savi, bins=100, color='lightgreen', edgecolor='black')
plt.title('Histogram Nilai SAVI')
plt.xlabel('Nilai SAVI')
plt.ylabel('Frekuensi Piksel')
plt.grid(True, alpha=0.5)
# Menggunakan bantuan garis vertikal untuk threshold
plt.axvline(x=0.2, color='r', linestyle='--', label='Contoh Threshold = 0.2')
plt.legend()
plt.show()

# ---- Melakukan thresholding ----
# Menentukan threshold vegetasi
print("Melakukan thresholding...")
manual_threshold = 0.2
thresholding = savi > manual_threshold
hasil_threshold = thresholding.astype(rasterio.uint8)
# Menyimpan hasil threshold
threshold_file_path = simpan_raster(hasil_threshold, profile, "Hasil/Threshold", "1.tif")

# ---- Melakukan masking ----
# Masking kanal green, red, red_edge, dan nir
# Memuat file threshold
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
green_mask_path = simpan_raster(hasil_masking_green, profile, "Hasil/Mask", "green.tif", nodata_value=-9999)
red_mask_path = simpan_raster(hasil_masking_red, profile, "Hasil/Mask", "red.tif", nodata_value=-9999)
red_edge_mask_path = simpan_raster(hasil_masking_red_edge, profile, "Hasil/Mask", "red_edge.tif", nodata_value=-9999)
nir_mask_path = simpan_raster(hasil_masking_nir, profile, "Hasil/Mask", "nir.tif", nodata_value=-9999)

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
ndvi_file_path = simpan_raster(transform_ndvi, profile, "Hasil/Transformasi/NDVI","NDVI_1.tif")
ukuran_raster(clipped_file_path)
ukuran_raster(savi_file_path)
ukuran_raster(threshold_file_path)
ukuran_raster(green_mask_path)
ukuran_raster(red_mask_path)
ukuran_raster(red_edge_mask_path)
ukuran_raster(nir_mask_path)
ukuran_raster(ndvi_file_path)
print('aman aja')
    