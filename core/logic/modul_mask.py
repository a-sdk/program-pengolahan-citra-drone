"""
Modul untuk mask citra.
"""

import os
import glob
import numpy as np
import rasterio as rio
import logging

logger = logging.getLogger(__name__)
            
# Fungsi untuk melakukan masking pada setiap band terpisah
def mask_band_terpisah(input_folder, mask_path, output_folder, logika=lambda x: x==1, nilai_nodata=0):
    """
    Menerapkan masking pada band berdasarkan mask boolean.
    
    Parameters:
        input_folder (str): Lokasi folder raster yang akan di-mask.
        mask_path (str): Lokasi file mask.
        output_folder (str): Nama folder tempat hasil mask disimpan.
        logika (function): Fungsi lambda sebagai acuan mask.
        nilai_nodata (float): Nilai nodata raster.
    
    Returns:
        str: Output path.
    """
    with rio.open(mask_path) as src_mask:
        mask_data = src_mask.read(1)
    # Membuat boolean mask
    mask_valid = logika(mask_data)
    # Mengecualikan nilai nodata
    mask_valid[np.isnan(mask_data)] = False
    logger.info(f"Mask boolean berhasil dibuat. Total piksel valid: {np.sum(mask_valid)}")
    # Menerapkan mask pada semua file dalam input folder
    lst_file = glob.glob(os.path.join(input_folder, "*.tif"))
    # if not lst_file:
    #     print(f"Tidak ada file .tif di {input_folder}")
    os.makedirs(output_folder, exist_ok=True)
    # print(f"Menerapkan mask ke {len(lst_file)} band")
    for file in lst_file:
        nf = os.path.basename(file)
        output_path = os.path.join(output_folder, nf)
        with rio.open(file) as src:
            data = src.read(1)
            profile = src.profile
        data[~mask_valid] = nilai_nodata
        profile.update(
            dtype="float32",
            nodata=nilai_nodata
        )
        print("Menyimpan hasil masking...")
        with rio.open(output_path, "w", **profile) as dest:
            dest.write(data, indexes=1)
        print(f"File {nf} berhasil disimpan di {output_folder}")
        return output_path

# Fungsi untuk melakukan masking pada tumpukan fitur
def mask_tumpukan_fitur(input_folder, mask_path, output_folder, logika=lambda x: x==1, nilai_nodata=0):
    """
    Menerapkan masking pada tumpukan fitur berdasarkan mask boolean.
    
    Parameters:
        input_folder (str): Lokasi folder tumpukan fitur yang akan di-mask.
        mask_path (str): Lokasi file mask.
        output_folder (str): Nama folder tempat hasil mask disimpan.
        logika (function): Fungsi lambda sebagai acuan mask.
        nilai_nodata (float): Nilai nodata raster.
    
    Returns:
        str: Output path.
    """
    with rio.open(mask_path) as src_mask:
            mask_data = src_mask.read(1)
    # Membuat boolean mask
    mask_valid = logika(mask_data)
    # Mengecualikan nilai nodata
    mask_valid[mask_data == nilai_nodata] = False           
    logger.info(f"Mask boolean berhasil dibuat. Total piksel valid: {np.sum(mask_valid)}")
    # print(f"Membuka tumpukan fitur...")
    nf = os.path.splitext(os.path.basename(input_folder))[0]
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, f"{nf}_masked.tif")
    with rio.open(input_folder) as src_data:
        # Membaca fitur sekaligus
        data_stack = src_data.read()
        profile = src_data.profile
        # print("Menerapkan mask ke semua fitur...")
        data_stack[:, ~mask_valid] = nilai_nodata
        
        # Perbarui profile untuk file output agar konsisten
        profile.update(
            dtype="uint16",
            count=data_stack.shape[0], 
            nodata=nilai_nodata
        )
        # print("Menyimpan hasil masking...")
        with rio.open(output_path, "w", **profile) as dest:
            dest.write(data_stack)
    # print(f"File {nf}_masked.tif berhasil disimpan di {output_folder}")
    return output_path
