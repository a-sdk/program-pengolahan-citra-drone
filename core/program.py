from modul_ekstraksi import (
    clip_raster, 
    ekstrak_koordinat_vertek,
    mask_band_terpisah, 
    mask_tumpukan_band, 
    ekstrak_piksel_setiap_koordinat, 
    ekstrak_tumpukan_fitur, 
    ekstrak_rerata_piksel
)
from modul_transformasi import (
    proses_segmentasi, 
    proses_transformasi
)
from utils import (
    ambil_file, 
    buat_multipoligon, 
    tumpuk_fitur, 
    cek_ukuran_raster
)
import rasterio as rio
import os
import numpy as np
import matplotlib.pyplot as plt
import time

########################################################
#
#            PROGRAM UTAMA
#
##########################################################
def main(mode_operasi="", mode_ekstraksi="mean"):
    print("\n==========================================================================")
    print("================= PROGRAM PENGOLAHAN CITRA MULTISPEKTRAL =================")
    print("==========================================================================")

    t0 = time.perf_counter()
    # ---- MENENTUKAN FOLDER KERJA ----
    # FOLDER INPUT
    lst_raster_input, lokasi_folder_raster = ambil_file(".tif")
    # Menentukan file .tif yang diproses berdasarkan input pengguna
    # raster_idx = int(input(f"Pilih file .tif: "))
    # raster_target = lst_raster_input[raster_idx - 1]
    # Menentukan file .shp yang diproses berdasarkan input pengguna
    shp_petak, _ = ambil_file(".shp")
    shp_idx = int(input(f"Pilih file .shp untuk acuan klip: "))
    shp_target = shp_petak[shp_idx - 1]

    for raster_file in lst_raster_input:
        t1 = time.perf_counter()   
        nf_raster = os.path.splitext(os.path.basename(raster_file))[0]
        print("="*50)
        print(f"\nMemproses file: {nf_raster}.tif")

        # FOLDER OUTPUT
        folder_hasil = rf"{lokasi_folder_raster}\Hasil\{nf_raster}_Files"
        folder_hasil_clip = rf"{folder_hasil}\Klip"
        folder_hasil_transformasi = rf"{folder_hasil}\Transformasi"
        folder_hasil_segmentasi = rf"{folder_hasil}\Segmentasi"
        folder_hasil_masking = rf"{folder_hasil}\Masking"
        folder_hasil_ekstraksi = rf"{folder_hasil}\Ekstraksi"
        folder_koord_vertek = rf"{folder_hasil}\Koordinat Vertek"
        # file_poligon_rumpun = r"C:\Users\acer_\Documents\Shapefiles\cikembar\rumpun\poligon_rumpun_lahan_2_30.shp"
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
            src_nodata = src_citra.nodata
            # Memisahkan bagian yang tidak valid
            mask_citra = src_citra.read_masks(1)
            # Membuat metadata profile
            src_profile = src_citra.profile
        # Menampilkan mask citra hasil clipping
        plt.figure(figsize=(8, 6)) # Tambahkan ini untuk ukuran plot yang lebih baik
        plt.title("Tampilan Mask Hasil Clipping")
        plt.imshow(mask_citra, cmap='gray') 
        # plt.show()

        # ---- EKSTRAK KOORDINAT VERTEK ----
        print("="*30)
        print("Pembuatan Komponen Poligon")
        print("="*30)
        jml_poly = int(input("Masukkan jumlah poligon: "))
        jml_subpoly = int(input("Masukkan jumlah komponen per poligon: "))
        file_multipoligon = buat_multipoligon(shp_target, jml_poly, jml_subpoly, folder_hasil)
        ekstrak_koordinat_vertek(file_multipoligon, folder_koord_vertek)

        # ---- PROSES TRANSFORMASI ----
        list_band = [red, green, blue, m_green, m_red, red_edge, nir]
        if mode_operasi != "pisah":
            gndvi, ndre, ndvi, savi = proses_transformasi(
                list_band, 
                src_profile, 
                folder_hasil_transformasi, 
                nilai_nodata=np.nan, 
                mode=""
            )
        elif mode_operasi == "pisah":
            gndvi, ndre, ndvi, savi = proses_transformasi(
                list_band, 
                src_profile, 
                folder_hasil_transformasi, 
                nilai_nodata=np.nan, 
                mode="pisah"
            )

        # ---- PROSES SEGMENTASI ----
        list_fitur = [clipped_raster, gndvi, ndre, ndvi, savi]
        threshold_padi = proses_segmentasi(list_fitur, src_profile, folder_hasil_segmentasi, nilai_nodata=np.nan)
        # Menumpuk fitur untuk hasil 11 fitur
        if mode_operasi != "pisah":
            lokasi_tumpukan_band = tumpuk_fitur(list_fitur, folder_hasil_transformasi, "tumpukan_fitur.tif")

        # ---- PROSES MASKING ----
        # Melakukan masking pada setiap band dan hasil transformasi
        if mode_operasi != "pisah":
            mask_tumpukan_band(
                lokasi_tumpukan_band, 
                threshold_padi, 
                folder_hasil_masking, 
                nilai_nodata=np.nan
            )
        elif mode_operasi == "pisah":
            mask_band_terpisah(
                folder_hasil_transformasi, 
                threshold_padi, 
                folder_hasil_masking, 
                nilai_nodata=np.nan
            )

        # ---- PROSES EKSTRAKSI ----
        # Mengekstrak piksel setiap band dari file terpisah berdasarkan koordinat verteks
        if mode_operasi == "pisah" and mode_ekstraksi == "all":
            ekstrak_piksel_setiap_koordinat(
                folder_koord_vertek, 
                folder_hasil_masking, 
                f"{folder_hasil_ekstraksi}/Pisah"
            )
        # Mengekstrak piksel dari tumpukan fitur
        elif mode_operasi != "pisah" and mode_ekstraksi == "all":
            ekstrak_tumpukan_fitur(
                file_multipoligon, 
                folder_hasil_masking, 
                f"{folder_hasil_ekstraksi}/Tumpuk", 
                f"Hasil_Ekstraksi_{nf_raster}.csv"
            )
        elif mode_operasi == "pisah" and mode_ekstraksi == "mean":
                ekstrak_rerata_piksel(
                file_multipoligon, 
                folder_hasil_masking, 
                f"{folder_hasil_ekstraksi}/Pisah", 
                f"Hasil_Ekstraksi_{nf_raster}_mean.csv"
            )   
        # Mengekstrak rata rata nilai piksel dalam multi poligon
        elif mode_operasi != "pisah" and mode_operasi == "mean":
            ekstrak_rerata_piksel(
                file_multipoligon, 
                folder_hasil_masking, 
                f"{folder_hasil_ekstraksi}/Tumpuk", 
                f"Hasil_Ekstraksi_{nf_raster}_mean.csv"
            )
        
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
            print(f"Selesai memproses {nf_raster} dalam {menit:d} menit {ts:3.2f} detik")

    # Waktu keseluruhan
    t2 = time.perf_counter()
    t = t2 - t0
    if t < 60:
        print(f"\nSelesai memproses {len(lst_raster_input)} file dalam {t:3.2f} detik")
    else:
        menit = int(t // 60)
        ts = t % 60
        print(f"\nSelesai memproses {len(lst_raster_input)} file dalam {menit:d} menit {ts:3.2f} detik")

    print("aman aja 🗣")


if __name__ == "__main__":
    operasi = "" # "pisah" atau kosongkan
    ekstrak_mode = "all" # untuk rata rata piksel atau "all" untuk semua piksel
    main(mode_operasi=operasi, mode_ekstraksi=ekstrak_mode)