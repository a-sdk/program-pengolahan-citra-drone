'''
Modul untuk mentransformasi citra
menggunakan beberapa indeks vegetasi.
'''

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
