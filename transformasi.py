'''
Modul untuk transformasi dan segmentasi.
'''

import numpy as np
import rasterio as rio
from utils import otsu_threshold, simpan_raster, tampilkan_histogram, tumpuk_fitur
from klasifikasi import pisahkan_gulma

def hitung_savi(nir_band, red_band, L):
    """
    Mentranformasi citra menggunakan Soil-Adjusted Vegetation Index.
    
    Args:
        nir_band (np.ndarray): Array NumPy berisi kanal NIR.
        red_band (np.ndarray): Array NumPy berisi kanal Red.
        L (float): Faktor koreksi kecerahan tanah (0 - 1).
    
    Returns:
        np.ndarray: Array NumPy SAVI.
    """
    # Normalisasi nilai piksel
    nir_band_norm = nir_band / np.float32(65535.0)
    red_band_norm = red_band / np.float32(65535.0)
    # Hindari pembagian dengan nol
    with np.errstate(divide='ignore', invalid='ignore'):
        savi = ((nir_band_norm.astype("float32") - red_band_norm.astype("float32")) * (1 + L)) / (nir_band_norm.astype("float32") + red_band_norm.astype("float32") + L) 
        # savi = np.nan_to_num(savi, nan = 0) # Mengganti nilai NaN dengan 0 atau nilai lain
    return savi

def hitung_ndvi(nir_band, red_band):
    """
    Mentranformasi citra menggunakan Normalized Difference Vegetation Index.
    
    Args:
        nir_band (np.ndarray): Array NumPy berisi kanal NIR.
        red_band (np.ndarray): Array NumPy berisi kanal Red.
        
    Returns:
        np.ndarray: Array NumPy NDVI.
    """
    nir_band_norm = nir_band / np.float32(65535.0)
    red_band_norm = red_band / np.float32(65535.0)
    # Hindari pembagian dengan nol
    with np.errstate(divide='ignore', invalid='ignore'):
        ndvi = (nir_band_norm.astype("float32") - red_band_norm.astype("float32")) / (nir_band_norm.astype("float32") + red_band_norm.astype("float32"))
        # ndvi = np.nan_to_num(ndvi, nan = 0) # Mengganti nilai NaN dengan 0 atau nilai lain
    return ndvi

def hitung_gndvi(nir_band, green_band):
    """
    Mentranformasi citra menggunakan Green Normalized Difference Vegetation Index.
    
    Args:
        nir_band (np.ndarray): Array NumPy berisi kanal NIR.
        green_band (np.ndarray): Array NumPy berisi kanal Green.
        
    Returns:
        np.ndarray: Array NumPy GNDVI.
    """
    nir_band_norm = nir_band / np.float32(65535.0)
    green_band_norm = green_band / np.float32(65535.0)
    # Hindari pembagian dengan nol
    with np.errstate(divide='ignore', invalid='ignore'):
        gndvi = (nir_band_norm.astype("float32") - green_band_norm.astype("float32")) / (nir_band_norm.astype("float32") + green_band_norm.astype("float32"))
        # gndvi = np.nan_to_num(gndvi, nan = 0) # Mengganti nilai NaN dengan 0 atau nilai lain
    return gndvi

def hitung_ndrei(nir_band, red_edge_band):
    """
    Mentranformasi citra menggunakan Normalized Difference Red Edge Index.
    
    Args:
        nir_band (np.ndarray): Array NumPy berisi kanal NIR.
        red_edge_band (np.ndarray): Array NumPy berisi kanal Red Edge.
    
    Returns:
        np.ndarray: Array NumPy NDRE.
    """
    nir_band_norm = nir_band / np.float32(65535.0)
    red_edge_band_norm = red_edge_band / np.float32(65535.0)
    # Hindari pembagian dengan nol
    with np.errstate(divide='ignore', invalid='ignore'):
        ndre = (nir_band_norm.astype("float32") - red_edge_band_norm.astype("float32")) / (nir_band_norm.astype("float32") + red_edge_band_norm.astype("float32"))
        # ndre = np.nan_to_num(ndre, nan = 0) # Mengganti nilai NaN dengan 0 atau nilai lain
    return ndre

# Fungsi untuk melakukan proses transformasi
def proses_transformasi(lst_band, profile, output_folder, nilai_nodata, mode=""):
    """
    Melakukan proses transformasi indeks vegetasi.
    
    Args:
        lst_band (list): List semua band yang digunakan.
        profile (dict): Metadata raster dari file sumber.
        output_folder (str): Nama folder tempat hasil transformasi disimpan.
        nilai_nodata (float): Nilai nodata raster.
        mode (str): Mode oprasi.
    
    Returns:
        str: gndvi_file_path, ndrei_file_path, ndvi_file_path, savi_file_path.
    """
    # Memuat setiap band
    red = lst_band[0]
    green = lst_band[1]
    blue = lst_band[2]
    m_green = lst_band[3]
    m_red = lst_band[4]
    red_edge = lst_band[5]
    nir = lst_band[6]
    print("Menghitung transformasi indeks vegetasi...")
    profile.update(
        dtype="float32",
        count=1
    )
    # Mentransformasi citra
    transform_savi = hitung_savi(nir, m_red, L=0.5)
    transform_ndrei = hitung_ndrei(nir, red_edge)
    transform_ndvi = hitung_ndvi(nir, m_red)
    transform_gndvi = hitung_gndvi(nir, m_green)
    # Menyimpan setiap band dan hasil transformasi ke dalam file GeoTIFF
    savi_file_path = simpan_raster(transform_savi, profile, output_folder, "SAVI.tif", nilai_nodata)
    ndrei_file_path = simpan_raster(transform_ndrei, profile, output_folder, "NDREI.tif", nilai_nodata)
    ndvi_file_path = simpan_raster(transform_ndvi, profile, output_folder, "NDVI.tif", nilai_nodata)
    gndvi_file_path = simpan_raster(transform_gndvi, profile, output_folder, "GNDVI.tif", nilai_nodata)
    if mode == "pisah":
        simpan_raster(red, profile, output_folder, "RED.tif", nilai_nodata)
        simpan_raster(green, profile, output_folder, "GREEN.tif", nilai_nodata)
        simpan_raster(blue, profile, output_folder, "BLUE.tif", nilai_nodata)
        simpan_raster(m_green, profile, output_folder, "M_GREEN.tif", nilai_nodata)
        simpan_raster(m_red, profile, output_folder, "M_RED.tif", nilai_nodata)
        simpan_raster(red_edge, profile, output_folder, "RED_EDGE.tif", nilai_nodata)
        simpan_raster(nir, profile, output_folder, "NIR.tif", nilai_nodata)
    
    return gndvi_file_path, ndrei_file_path, ndvi_file_path, savi_file_path


# Fungsi untuk melakukan proses segmentasi
def proses_segmentasi(lst_fitur, profile, output_folder, nilai_nodata):
    """
    Melakukan proses segmentasi untuk memisahkan tanaman padi.

    Args:
        lst_fitur (list): Fitur yang akan digunakan.
        profile (dict): Metadata raster dari file sumber.
        output_folder (str): Nama folder tempat hasil transformasi disimpan.
        nilai_nodata (float): Nilai nodata raster.

    Returns:
        str: threshold_file_path.
    """
    # Menumpuk fitur untuk segmentasi gulma
    # lokasi_tumpukan_band = tumpuk_fitur(lst_fitur, output_folder, "tumpukan_fitur.tif")
    # Membuat peta segmentasi gulma dan padi
    peta_segmentasi_gulma = pisahkan_gulma("model_random_forest.joblib", lst_fitur[0], output_folder, "segmentasi_gulma.tif", nilai_nodata)
    print("Memuat file SAVI...")
    with rio.open(lst_fitur[4]) as src_savi, rio.open(peta_segmentasi_gulma) as src_gulma, rio.open(lst_fitur[2]) as src_ndrei:
        savi = src_savi.read(1).astype("float32")
        ndrei = src_ndrei.read(1).astype("float32")
        mask_padi = src_gulma.read(1).astype("float32") < 2
    # Membaca SAVI dan NDREI lalu menampilkan histogram
    savi_1d = savi.ravel() 
    ndrei_1d = ndrei.ravel()    
    # Menampilkan histogram SAVI
    t_savi = otsu_threshold(savi, jumlah_bin=256, rentang_nilai=(-1, 1))
    t_ndrei = -0.05
    # tampilkan_histogram("SAVI", savi_1d, t_savi)
    # tampilkan_histogram("NDREI", ndrei_1d, t_ndrei)

    mask_savi = savi > t_savi
    mask_ndrei = ndrei > t_ndrei
    mask_final = mask_savi & mask_padi
    mask_final_indeks = mask_savi & mask_ndrei
    print(f"Melakukan thresholding SAVI dengan batas {t_savi}...")
    hasil_threshold = mask_final.astype("float32")
    hasil_threshold_2 = mask_final_indeks.astype("float32")
    # Menyimpan hasil threshold
    threshold_file_path = simpan_raster(hasil_threshold, profile, output_folder, "hasil_threshold_model.tif", nilai_nodata)
    # threshold2_file_path = simpan_raster(hasil_threshold_2, profile, output_folder, "hasil_threshold_indeks.tif", nilai_nodata)

    return threshold_file_path #, lokasi_tumpukan_band