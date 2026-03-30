from modul_ekstraksi import (
    potong_raster, 
    mask_tumpukan_fitur, 
    ekstrak_rerata_piksel
)
from modul_transformasi import (
    proses_segmentasi, 
    proses_transformasi
)
from modul_utilitas import ( 
    buat_multipoligon
)
from modul_klasifikasi import deteksi_penyakit_rumpun

import rasterio as rio
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolor
import matplotlib.patches as mpatch
import time

########################################################
#
#            PROGRAM UTAMA
#
##########################################################
def main(input_folder, poligon, model, scaler):
    print("\n==========================================================================")
    print("================= PROGRAM PENGOLAHAN CITRA MULTISPEKTRAL =================")
    print("==========================================================================")

    nf = os.path.splitext(os.path.basename(input_folder))[0]
    print(f"\nMemproses file: {nf}")
    t0 = time.perf_counter()
    # ---- MENENTUKAN FOLDER KERJA ----
    ROOT_FOLDER = rf"C:\Users\acer_\Documents\Orthomosaic\tes program skripsi\tes main"
    hasil_klip = rf"{ROOT_FOLDER}\hasil_klip"
    hasil_trf = rf"{ROOT_FOLDER}\hasil_trf"
    hasil_segs = rf"{ROOT_FOLDER}\hasil_segmentasi"
    hasil_mask = rf"{ROOT_FOLDER}\hasil_masking"
    hasil_ekstraksi = rf"{ROOT_FOLDER}\hasil_ekstraksi"
    hasil_deteksi = rf"{ROOT_FOLDER}\hasil_deteksi"
    
    # Buat multipoligon
    multipoligon = buat_multipoligon(shp_layer=poligon, jml_poligon=1, jml_komponen=1500, output_folder=ROOT_FOLDER)
    # Potong citra
    hasil_klip = potong_raster(input_folder, poligon, hasil_klip, "hasil_potong.tif", 0)
    with rio.open(hasil_klip) as src:
        m_green = src.read(4)
        m_red = src.read(5)
        red_edge = src.read(6)
        nir = src.read(7)
        src_nodata = src.nodata
        src_profile = src.profile
    kanal_ms = [m_green, m_red, red_edge, nir]
    # Transformasi
    ndvi = proses_transformasi(lst_band=kanal_ms, profile=src_profile, output_folder=hasil_trf, nilai_nodata=src_nodata)
    fitur = [hasil_klip, ndvi]
    # Segmentasi
    mask_vegetasi = proses_segmentasi(lst_fitur=fitur, profile=src_profile, output_folder=hasil_segs, nilai_nodata=src_nodata)
    # Masking
    mask_tumpukan_fitur(input_folder=hasil_klip, mask_path=mask_vegetasi, output_folder=hasil_mask, nilai_nodata=src_nodata)
    # Ekstrak
    ekstrak_rerata_piksel(shp_layer=multipoligon, input_folder=hasil_mask, output_folder=hasil_ekstraksi, output_filename=f"rerata_nilai_piksel.csv")
    # Deteksi penyakit
    blas, blb, bs, nbs = deteksi_penyakit_rumpun(model_path=model, scaler_path=scaler, input_folder=hasil_mask, output_folder=hasil_deteksi)

    # Waktu keseluruhan (timer)
    t2 = time.perf_counter()
    t = t2 - t0
    if t < 60:
        print(f"\nSelesai memproses dalam {t:3.2f} detik")
    else:
        menit = int(t // 60)
        ts = t % 60
        print(f"\nSelesai memproses dalam {menit:d} menit {ts:3.2f} detik")

    print("Menampilkan hasil...")
    alpha = "#00000000"
    hg = "#008000ff"
    ht = "#90ee90ff"
    kuning = "#ffff74ff"
    merah = "#d7191cff"
    warna = [alpha, hg, ht, kuning, merah]
    cmaps = mcolor.ListedColormap(warna)
    patch_hg = mpatch.Patch(color=hg, label="Sehat", ec="black")
    patch_ht = mpatch.Patch(color=ht, label="Ringan", ec="black")
    patch_k = mpatch.Patch(color=kuning, label="Sedang", ec="black")
    patch_m = mpatch.Patch(color=merah, label="Parah", ec="black")
    plt.legend(handles=[patch_hg, patch_ht, patch_k, patch_m], bbox_to_anchor=(1.05, 1), loc="best")
    plt.title("Hasil Deteksi Serangan Penyakit Blas")
    with rio.open(blas) as src:
        data = src.read(1) 
        plt.imshow(data, cmap=cmaps) 
        plt.show()


if __name__ == "__main__":
    POLY_PATH = r"C:\Users\acer_\Documents\Shapefiles\cikembar\Lahan 2_0.shp"
    RASTER_PATH = r"C:\Users\acer_\Documents\Orthomosaic\tes program skripsi\HST 29 36_PAGI_30.tif" 
    MODEL_PATH = r"core\models\model_deteksi_penyakit_v1.keras"
    SCALER_PATH = r"core\scaler\MinMaxScaler_v1.joblib"
    main(input_folder=rf"{RASTER_PATH}", 
         poligon=POLY_PATH, 
         model=MODEL_PATH, 
         scaler=SCALER_PATH
         )