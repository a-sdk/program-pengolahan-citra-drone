'''
Pustaka untuk mentransformasi citra
menggunakan beberapa indeks vegetasi.
'''
# Changelog: 
# 2025/08/06 - Versi awal

# Libraries
import numpy as np

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
    # Hindari pembagian dengan nol
    with np.errstate(divide='ignore', invalid='ignore'):
        savi = ((nir_band.astype(float) - red_band.astype(float)) * (1 + L)) / (nir_band.astype(float) + red_band.astype(float) + L) 
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
    # Hindari pembagian dengan nol
    with np.errstate(divide='ignore', invalid='ignore'):
        ndvi = (nir_band.astype(float) - red_band.astype(float)) / (nir_band.astype(float) + red_band.astype(float))
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
    # Hindari pembagian dengan nol
    with np.errstate(divide='ignore', invalid='ignore'):
        gndvi = (nir_band.astype(float) - green_band.astype(float)) / (nir_band.astype(float) + green_band.astype(float))
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
    # Hindari pembagian dengan nol
    with np.errstate(divide='ignore', invalid='ignore'):
        ndre = (nir_band.astype(float) - red_edge_band.astype(float)) / (nir_band.astype(float) + red_edge_band.astype(float))
        # ndre = np.nan_to_num(ndre, nan = 0) # Mengganti nilai NaN dengan 0 atau nilai lain
    return ndre
