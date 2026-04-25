import pandas as pd
import numpy as np

import numpy as np
import pandas as pd

import pandas as pd
import numpy as np

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

csv = r"C:\Users\acer_\Documents\Orthomosaic\tes aplikasi\Lahan percobaan\hasil_ekstrak.csv"
df = pd.read_csv(csv)
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
data_final.to_csv("contoh hasil.csv", index=False)
print("Tamat")
