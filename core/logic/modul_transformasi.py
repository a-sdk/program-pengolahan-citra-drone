"""
Modul untuk transformasi dan segmentasi.
"""

import numpy as np
import pandas as pd
import rasterio as rio
from core.logic.modul_utilitas import otsu_threshold, simpan_raster, tampilkan_histogram
from core.logic.modul_klasifikasi import pisahkan_gulma
import logging
import os

logger = logging.getLogger(__name__)

def safe_div(num, denom):
    with np.errstate(divide='ignore', invalid='ignore'):
        res = num / denom
    val = np.where(np.isfinite(res), res, 0.0)
    return float(val) if np.isscalar(val) or val.size == 1 else val.astype(float)

def trim_norm_df(df, low_per=10, high_per=90):
    data_array = df.values.astype(float)
    # Filter data untuk mencari ambang batas
    valid_mask = (data_array > 0) & (~np.isnan(data_array))
    valid_data = data_array[valid_mask]

    if valid_data.size == 0:
        return df 
    
    low_val, high_val = np.percentile(valid_data, [low_per, high_per])
    
    # Proses Trimming & Normalisasi
    trimmed_array = np.clip(data_array, low_val, high_val)
    normalized_array = trimmed_array / 65535.0
    return pd.DataFrame(normalized_array, columns=df.columns)

def hitung_savi(nir, m_red, L):
    """
    Mentranformasi citra menggunakan Soil-Adjusted Vegetation Index.
    
    Parameters:
        nir (np.ndarray): Array NumPy berisi kanal NIR.
        m_red (np.ndarray): Array NumPy berisi kanal Multispectral Red.
        L (float): Faktor koreksi kecerahan tanah (0 - 1).
    
    Returns:
        np.ndarray: Array NumPy SAVI.
    """

    # Hindari pembagian dengan nol
    with np.errstate(divide='ignore', invalid='ignore'):
        savi = ((nir.astype(float) - m_red.astype(float)) * (1 + L)) / (nir.astype(float) + m_red.astype(float) + L)
    savi = np.nan_to_num(savi, nan=0.0, posinf=0.0, neginf=0.0) 
    return savi

def hitung_ndvi(nir, m_red):
    """
    Mentranformasi citra menggunakan Normalized Difference Vegetation Index.
    
    Parameters:
        nir (np.ndarray): Array NumPy berisi kanal NIR.
        m_red (np.ndarray): Array NumPy berisi kanal Multispectral Red.
        
    Returns:
        np.ndarray: Array NumPy NDVI.
    """

    ndvi = safe_div(nir - m_red, nir + m_red)
    ndvi = np.nan_to_num(ndvi, nan=0.0, posinf=0.0, neginf=0.0)
    return ndvi

def hitung_gndvi(nir, m_green):
    """
    Mentranformasi citra menggunakan Green Normalized Difference Vegetation Index.
    
    Parameters:
        nir (np.ndarray): Array NumPy berisi kanal NIR.
        m_green (np.ndarray): Array NumPy berisi kanal Multispectral Green.
        
    Returns:
        np.ndarray: Array NumPy GNDVI.
    """
 
    gndvi = safe_div(nir - m_green, nir + m_green)
    gndvi = np.nan_to_num(gndvi, nan=0.0, posinf=0.0, neginf=0.0)
    return gndvi

def hitung_ndre(nir, red_edge):
    """
    Mentranformasi citra menggunakan Normalized Difference Red Edge Index.
    
    Parameters:
        nir (np.ndarray): Array NumPy berisi kanal NIR.
        red_edge (np.ndarray): Array NumPy berisi kanal Red Edge.
    
    Returns:
        np.ndarray: Array NumPy NDRE.
    """

    ndre = safe_div(nir - red_edge, nir + red_edge)
    ndre = np.nan_to_num(ndre, nan=0.0, posinf=0.0, neginf=0.0)
    return ndre

def hitung_evi(nir, m_red, blue):
    """
    Mentranformasi citra menggunakan Enhanced Vegetation Index.
    
    Parameters:
        nir (np.ndarray): Array NumPy berisi kanal NIR.
        m_red (np.ndarray): Array NumPy berisi kanal Multispectral Red.
        blue (np.ndarray): Array NumPy berisi kanal Blue.
    
    Returns:
        np.ndarray: Array NumPy EVI.
    """

    evi = np.clip(2.5 * safe_div(nir - m_red, (nir + 6 * m_red - 7.5 * blue + 1)), -1.0, 1.0)
    evi = np.nan_to_num(evi, nan=0.0, posinf=0.0, neginf=0.0)
    return evi

def hitung_vidvi(red, green, blue):
    """
    Mentranformasi citra menggunakan VIDVI.
    
    Parameters:
        red (np.ndarray): Array NumPy berisi kanal Red.
        green (np.ndarray): Array NumPy berisi kanal Green.
        blue (np.ndarray): Array NumPy berisi kanal Blue.
    
    Returns:
        np.ndarray: Array NumPy VIDVI.
    """

    vidvi = safe_div(2 * green - red - blue, 2 * green + red + blue)
    vidvi = np.nan_to_num(vidvi, nan=0.0, posinf=0.0, neginf=0.0)
    return vidvi

def hitung_cive(red, green, blue):
    """
    Mentranformasi citra menggunakan CIVE.
    
    Parameters:
        red (np.ndarray): Array NumPy berisi kanal Red.
        green (np.ndarray): Array NumPy berisi kanal Green.
        blue (np.ndarray): Array NumPy berisi kanal Blue.
    
    Returns:
        np.ndarray: Array NumPy CIVE.
    """
    cive = (0.441 * red) - (0.81 * green) + (0.385 * blue) + 18.7874
    cive = np.nan_to_num(cive, nan=0.0, posinf=0.0, neginf=0.0)
    return cive

# Fungsi untuk melakukan proses transformasi
def persiapan_segmentasi(input_folder, output_folder, nilai_nodata=0):
    """
    Melakukan tranformasi NDVI untuk segmentasi.
    
    Parameters:
        input_folder (str): Lokasi file raster.
        output_folder (str): Nama folder tempat hasil transformasi disimpan.
        nilai_nodata (float): Nilai nodata raster.
    
    Returns:
        str: ndvi_file_path.
    """
    # Memuat band
    with rio.open(input_folder) as src:
        m_red = src.read(5)
        nir = src.read(7)
        profile = src.profile

    print("\nMenghitung transformasi indeks vegetasi...")
    profile.update(
        dtype="float32",
        count=1
    )
    # Mentransformasi citra
    transform_ndvi = hitung_ndvi(nir, m_red)
    ndvi_file_path = simpan_raster(transform_ndvi, profile, output_folder, "NDVI.tif", nilai_nodata)
    return ndvi_file_path 

def proses_transformasi(input_folder, output_folder):
    """
    Melakukan proses transformasi indeks vegetasi.

    Parameters:
        input_folder (str): Lokasi file csv hasil ekstrak.
        output_folder (str): Lokasi folder ouptut.

    Returns:
        str: Output path.
    """
    os.makedirs(output_folder, exist_ok=True)
    output_path = f"{output_folder}/hasil_ekstrak_piksel.csv"
    df = pd.read_csv(input_folder)
    bands = ["RED", "GREEN", "BLUE", "M_GREEN", "M_RED", "RED_EDGE", "NIR"]
    data_trimmed = trim_norm_df(df[bands].copy())
    cols_identitas = ["id", "Nama", "X", "Y"]

    # Terapkan urutan
    data_trimmed["CIVE"]  = hitung_cive(data_trimmed["RED"], data_trimmed["GREEN"], data_trimmed["BLUE"])
    data_trimmed["EVI"]   = hitung_evi(data_trimmed["NIR"], data_trimmed["M_RED"], data_trimmed["BLUE"])
    data_trimmed["GNDVI"] = hitung_gndvi(data_trimmed["NIR"], data_trimmed["GREEN"])
    data_trimmed["NDRE"]  = hitung_ndre(data_trimmed["NIR"], data_trimmed["RED_EDGE"])
    data_trimmed["NDVI"]  = hitung_ndvi(data_trimmed["NIR"], data_trimmed["RED"]) # 
    data_trimmed["VIDVI"] = hitung_vidvi(data_trimmed["RED"], data_trimmed["GREEN"], data_trimmed["BLUE"])

    for col in cols_identitas:
        data_trimmed[col] = df[col]

    cols_indeks = ["CIVE", "EVI", "GNDVI", "NDRE", "NDVI", "VIDVI"]
    urutan_final = cols_identitas + bands + cols_indeks
    data_final = data_trimmed[urutan_final]
    data_final.to_csv(output_path, index=False)
    os.remove(input_folder)
    return output_path

# Fungsi untuk melakukan proses segmentasi
def proses_segmentasi(input_folder, ndvi_path, output_folder, check_cancel, on_progress, nilai_nodata=0):
    """
    Melakukan proses segmentasi untuk memisahkan tanaman padi.

    Parameters:
        input_folder (str): Lokasi file raster.
        ndvi_path (str): Lokasi file raster NDVI.
        output_folder (str): Nama folder tempat hasil transformasi disimpan.
        nilai_nodata (float): Nilai nodata raster.

    Returns:
        str: threshold_file_path.
    """

    # Membuat peta segmentasi gulma dan padi
    model_gulma = r"core\models\model_deteksi_gulma_v1.joblib"
    peta_segmentasi_gulma = pisahkan_gulma(model_gulma, input_folder, output_folder, "segmentasi_gulma.tif", check_cancel, on_progress)
    print("Memuat file hasil transformasi...")
    with (
        rio.open(ndvi_path) as src_ndvi,
        rio.open(peta_segmentasi_gulma) as src_gulma
    ):
        ndvi = src_ndvi.read(1).astype(float)
        mask_padi = src_gulma.read(1).astype(float) == 1
        profile = src_ndvi.profile
    
    # Menghitung threshold indeks vegetasi
    # t_ndre = otsu_threshold(ndre, jumlah_bin=256, rentang_nilai=(-1, 1))
    t_ndvi = otsu_threshold(ndvi, jumlah_bin=256, rentang_nilai=(-1, 1))
    # t_savi = otsu_threshold(savi, jumlah_bin=256, rentang_nilai=(-1, 1))

    # Menampilkan histogram (opsional)
    # ndre_1d = ndre.ravel()    
    # ndvi_1d = ndvi.ravel()    
    # savi_1d = savi.ravel() 
    # tampilkan_histogram("NDRE", ndre_1d, t_ndre)
    # tampilkan_histogram("NDVI", ndre_1d, t_ndvi)
    # tampilkan_histogram("SAVI", savi_1d, t_savi)

    # Thresholding
    mask_ndvi = ndvi > t_ndvi
    mask_final = mask_ndvi & mask_padi
    print(f"Menghitung ambang NDVI dengan batas {t_ndvi}...")
    hasil_threshold = mask_final.astype(float)

    # Menyimpan hasil threshold
    threshold_file_path = simpan_raster(hasil_threshold, profile, output_folder, "hasil_threshold_model.tif", nilai_nodata)
    os.remove(peta_segmentasi_gulma)
    return threshold_file_path