from ekstraksi import clip_raster, mask_band_terpisah, mask_tumpukan_band, ekstrak_piksel_dari_vertek, ekstrak_tumpukan_fitur
from transformasi import proses_segmentasi, proses_transformasi
from utils import ambil_file, cek_ukuran_raster
import rasterio as rio
import os
import matplotlib.pyplot as plt
import time

########################################################
#
#            PROGRAM UTAMA
#
##########################################################
t0 = time.perf_counter()
# ---- MENENTUKAN FOLDER KERJA ----
# FOLDER INPUT
lst_raster_input, lokasi_folder_raster = ambil_file(".tif")
# Menentukan file .tif yang diproses berdasarkan input pengguna
# raster_idx = int(input(f"Pilih file .tif: "))
# raster_target = lst_raster_input[raster_idx - 1]
# Menentukan file .shp yang diproses berdasarkan input pengguna
shp_input, lokasi_folder_shp = ambil_file(".shp")
shp_idx = int(input(f"Pilih file .shp untuk clipping: "))
shp_target = shp_input[shp_idx - 1]



for raster_file in lst_raster_input:
    t1 = time.perf_counter()   
    nf_raster = os.path.splitext(os.path.basename(raster_file))[0]
    print("\n====================================================")
    print(f"\nMemproses {nf_raster}...")

    # FOLDER OUTPUT
    folder_hasil_clip = rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Klip"
    folder_hasil_transformasi = rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Transformasi"
    folder_hasil_segmentasi = rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Segmentasi"
    folder_hasil_masking = rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files\Masking"
    folder_hasil_ekstraksi = r"C:\Users\acer_\Documents\Hasil_Ekstraksi" # rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files"

    # ---- PROSES CLIPPING AWAL ----
    # Memotong petakan sawah berdasarkan poligon
    clipped_raster = clip_raster(raster_file, shp_target, folder_hasil_clip, f"{nf_raster}_clip.tif")
    # Mengakses citra beserta band yang diperlukan 
    print("\nMembaca band yang diperlukan...")
    with rio.open(clipped_raster) as src_citra:
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
        # Membuat metadata profile
        profile = src_citra.profile
    # Menampilkan mask citra hasil clipping
    plt.figure(figsize=(8, 6)) # Tambahkan ini untuk ukuran plot yang lebih baik
    plt.title("Tampilan Mask Hasil Clipping")
    plt.imshow(mask_citra, cmap='gray') 
    # plt.show()

    # ---- PROSES TRANSFORMASI ----
    lst_band = [red, green, blue, m_green, m_red, red_edge, nir]
    gndvi, ndrei, ndvi, savi = proses_transformasi(lst_band, profile, folder_hasil_transformasi, nilai_nodata=nodata_asli, mode="")

    # ---- PROSES SEGMENTASI ----
    lst_fitur = [clipped_raster, gndvi, ndrei, ndvi, savi]
    tumpukan_band, threshold_padi = proses_segmentasi(lst_fitur, profile, folder_hasil_segmentasi, nilai_nodata=nodata_asli)


    # ---- PROSES MASKING ----
    # Melakukan masking pada setiap band dan hasil transformasi
    # mask_band_terpisah(folder_hasil_transformasi, threshold_padi, folder_hasil_masking, nilai_nodata=nodata_asli)
    mask_tumpukan_band(tumpukan_band, threshold_padi, folder_hasil_masking, nilai_nodata=nodata_asli)

    # ---- PROSES EKSTRAKSI ----
    file_vertek = r"C:\Users\acer_\Documents\Shapefiles\verteks_poligon_rumpun_lahan_2.csv"  # File koordinat vertek poligon
    file_shp = r"C:\Users\acer_\Documents\Shapefiles\poligon_rumpun_lahan_2.shp" # File poligon rumpun
    # Mengekstrak piksel setiap band dari file terpisah berdasarkan koordinat verteks
    # ekstrak_piksel_dari_vertek(file_vertek, folder_hasil_masking, folder_hasil_ekstraksi, f"Hasil_Ekstraksi_{nf_raster}.csv")
    # Mengekstrak piksel dari tumpukan fitur
    ekstrak_tumpukan_fitur(file_shp, folder_hasil_masking, folder_hasil_ekstraksi, f"{nf_raster}.csv")
    
    # ---- PROSES TAMBAHAN ----
    # Menghitung ukuran raster 
    # cek_ukuran_raster(tumpukan_band)

    # Waktu setiap proses (per iterasi)
    t2 = time.perf_counter()
    t = t2 - t1
    if t < 60:
        print(f"Selesai memproses {nf_raster} dalam {t: 3.2f} detik")
    else:
        menit = int(t // 60)
        ts = t % 60
        print(f"Selesai memproses {nf_raster} dalam {menit:d} menit {ts: 3.2f} detik")

# Waktu keseluruhan
t2 = time.perf_counter()
t = t2 - t0
if t < 60:
    print(f"\nSelesai memproses {len(lst_raster_input)} file dalam {t: 3.2f} detik")
else:
    menit = int(t // 60)
    ts = t % 60
    print(f"\nSelesai memproses {len(lst_raster_input)} file dalam {menit:d} menit {ts: 3.2f} detik")

print('aman aja')