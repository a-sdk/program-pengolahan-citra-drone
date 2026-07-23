"""
Modul untuk mask citra.
"""

import os
import numpy as np
import rasterio as rio
import logging

logger = logging.getLogger(__name__)
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
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, "mask result.tif")
    with rio.open(input_folder) as src_data:
        # Membaca fitur sekaligus
        data_stack = src_data.read()
        profile = src_data.profile
        # print("Menerapkan mask ke semua fitur...")
        data_stack[:, ~mask_valid] = nilai_nodata
        
        # Perbarui profile untuk file output agar konsisten
        profile.update(
            dtype="float32",
            count=data_stack.shape[0], 
            nodata=nilai_nodata
        )
        # print("Menyimpan hasil masking...")
        with rio.open(output_path, "w", **profile) as dest:
            dest.write(data_stack)
    # print(f"File {nf}_masked.tif berhasil disimpan di {output_folder}")
    return output_path
