from app.result_model import AnalysisResult
from core.modul_ekstraksi import (
    potong_raster, 
    mask_tumpukan_fitur, 
    ekstrak_rerata_piksel
)
from core.modul_transformasi import (
    proses_segmentasi, 
    proses_transformasi
)
from core.modul_utilitas import ( 
    buat_multipoligon,
    tampilkan_penyakit,
    hitung_sebaran
)
from core.modul_klasifikasi import deteksi_penyakit_rumpun

import rasterio as rio
import os
import time

class AnalysisController:
    def run(self, raw_tif_path, shp_path=None):
        result = AnalysisResult()
        result.original_path = raw_tif_path
        # 1. Tahap Clipping
        # Output: path ke file .tif yang sudah dipotong
        if shp_path:
            clipped_path = potong_raster.run(raw_tif_path, shp_path)
        else:
            clipped_path = raw_tif_path

        # 2. Tahap Transformasi (NDVI, GNDVI, dll)
        # Input: clipped_path, Output: path ke folder/file hasil transformasi
        trans_output_path = transform_logic.run(clipped_path)

        # 3. Tahap Segmentasi & Klasifikasi
        # Input: trans_output_path, Output: path ke file klasifikasi/mask
        mask_path = segment_logic.run(trans_output_path)
        
        # 4. Tahap Ekstraksi Fitur (biasanya berupa CSV atau JSON)
        feature_path = extract_logic.run(mask_path)

        # Mengembalikan objek yang berisi semua 'alamat' file hasil
        return AnalysisResult(
            original_path=raw_tif_path,
            processed_path=mask_path,
            report_path=feature_path
        )