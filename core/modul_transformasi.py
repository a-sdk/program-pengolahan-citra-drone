"""
Modul untuk transformasi dan segmentasi.
"""

import numpy as np
import rasterio as rio
from core.modul_utilitas import otsu_threshold, simpan_raster, tampilkan_histogram
from core.modul_klasifikasi import pisahkan_gulma
import logging
import os

logger = logging.getLogger(__name__)

def hitung_savi(nir_band, red_band, L):
    """
    Mentranformasi citra menggunakan Soil-Adjusted Vegetation Index.
    
    Parameters:
        nir_band (np.ndarray): Array NumPy berisi kanal NIR.
        red_band (np.ndarray): Array NumPy berisi kanal Red.
        L (float): Faktor koreksi kecerahan tanah (0 - 1).
    
    Returns:
        np.ndarray: Array NumPy SAVI.
    """

    # Hindari pembagian dengan nol
    with np.errstate(divide='ignore', invalid='ignore'):
        savi = ((nir_band.astype(float) - red_band.astype(float)) * (1 + L)) / (nir_band.astype(float) + red_band.astype(float) + L)
    savi = np.nan_to_num(savi, nan=0.0, posinf=0.0, neginf=0.0) 
    return savi

def hitung_ndvi(nir_band, red_band):
    """
    Mentranformasi citra menggunakan Normalized Difference Vegetation Index.
    
    Parameters:
        nir_band (np.ndarray): Array NumPy berisi kanal NIR.
        red_band (np.ndarray): Array NumPy berisi kanal Red.
        
    Returns:
        np.ndarray: Array NumPy NDVI.
    """

    # Hindari pembagian dengan nol
    with np.errstate(divide='ignore', invalid='ignore'):
        ndvi = (nir_band.astype(float) - red_band.astype(float)) / (nir_band.astype(float) + red_band.astype(float))
    ndvi = np.nan_to_num(ndvi, nan=0.0, posinf=0.0, neginf=0.0)
    return ndvi

def hitung_gndvi(nir_band, green_band):
    """
    Mentranformasi citra menggunakan Green Normalized Difference Vegetation Index.
    
    Parameters:
        nir_band (np.ndarray): Array NumPy berisi kanal NIR.
        green_band (np.ndarray): Array NumPy berisi kanal Green.
        
    Returns:
        np.ndarray: Array NumPy GNDVI.
    """
 
    # Hindari pembagian dengan nol
    with np.errstate(divide='ignore', invalid='ignore'):
        gndvi = (nir_band.astype(float) - green_band.astype(float)) / (nir_band.astype(float) + green_band.astype(float))
    gndvi = np.nan_to_num(gndvi, nan=0.0, posinf=0.0, neginf=0.0)
    return gndvi

def hitung_ndre(nir_band, red_edge_band):
    """
    Mentranformasi citra menggunakan Normalized Difference Red Edge Index.
    
    Parameters:
        nir_band (np.ndarray): Array NumPy berisi kanal NIR.
        red_edge_band (np.ndarray): Array NumPy berisi kanal Red Edge.
    
    Returns:
        np.ndarray: Array NumPy NDRE.
    """

    # Hindari pembagian dengan nol
    with np.errstate(divide='ignore', invalid='ignore'):
        ndre = (nir_band.astype(float) - red_edge_band.astype(float)) / (nir_band.astype(float) + red_edge_band.astype(float))
    ndre = np.nan_to_num(ndre, nan=0.0, posinf=0.0, neginf=0.0)
    return ndre

class Transformer:
    """
    Kelas untuk mentransformasi citra.
    """
    def __init__(self):
        self.status = "Idle"
        self.last_result = None
    
    def run(self, input_folder, output_folder):
        self.status = "Processing"
        logger.info("Memulai proses transformasi...") 
        try:
            self.last_result = self.proses_transformasi(input_folder, output_folder) 
            self.status = "Done"
            return self.last_result
        except Exception as e:
            self.status = "Error"
            logger.error(f"ERROR {type(e).__name__}: {e}", exc_info=True)
            return None
        
    # Fungsi untuk melakukan proses transformasi
    def proses_transformasi(self, input_folder, output_folder, nilai_nodata=0):
        """
        Melakukan proses transformasi indeks vegetasi.
        
        Parameters:
            input_folder (str): Lokasi file raster.
            output_folder (str): Nama folder tempat hasil transformasi disimpan.
            nilai_nodata (float): Nilai nodata raster.
            mode (str): Mode oprasi.
        
        Returns:
            str: gndvi_file_path, ndre_file_path, ndvi_file_path, savi_file_path.
        """
        # Memuat band
        with rio.open(input_folder) as src:
            m_green = src.read(4)
            m_red = src.read(5)
            red_edge = src.read(6)
            nir = src.read(7)
            profile = src.profile

        print("\nMenghitung transformasi indeks vegetasi...")
        profile.update(
            dtype="float32",
            count=1
        )
        # Mentransformasi citra
        # transform_savi = hitung_savi(nir, m_red, L=0.5)
        # transform_ndre = hitung_ndre(nir, red_edge)
        # transform_gndvi = hitung_gndvi(nir, m_green)
        transform_ndvi = hitung_ndvi(nir, m_red)
        # Menyimpan setiap band dan hasil transformasi ke dalam file GeoTIFF
        # savi_file_path = simpan_raster(transform_savi, profile, output_folder, "SAVI.tif", nilai_nodata)
        # ndre_file_path = simpan_raster(transform_ndre, profile, output_folder, "ndre.tif", nilai_nodata)
        # gndvi_file_path = simpan_raster(transform_gndvi, profile, output_folder, "GNDVI.tif", nilai_nodata)
        ndvi_file_path = simpan_raster(transform_ndvi, profile, output_folder, "NDVI.tif", nilai_nodata)
        
        return ndvi_file_path # gndvi_file_path, ndre_file_path,  savi_file_path

class Segmenter:
    """
    Kelas untuk segmentasi citra.
    """
    def __init__(self):
        self.status = "Idle"
        self.last_result = None

    def run(self, input_folder, ndvi_path, output_folder, check_cancel=None, on_progress=None):
        self.status = "Processing"
        logger.info("Memulai proses segmentasi...") 
        try:
            self.last_result = self.proses_segmentasi(input_folder, ndvi_path, output_folder, check_cancel, on_progress) 
            self.status = "Done"
            return self.last_result
        except Exception as e:
            self.status = "Error"
            logger.error(f"ERROR {type(e).__name__}: {e}", exc_info=True)
            return None
        
    # Fungsi untuk melakukan proses segmentasi
    def proses_segmentasi(self, input_folder, ndvi_path, output_folder, check_cancel, on_progress, nilai_nodata=0):
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



if __name__ == "__main__":
    path_hasil = r"C:\Users\acer_\Documents\Orthomosaic\tes program skripsi\hasil_trf2"
    path_tif = r"C:\Users\acer_\Documents\Orthomosaic\tes program skripsi\klip\hasil_potong.tif"
    path_poly = r"C:\Users\acer_\Documents\Shapefiles\cikembar\Lahan 2_0.shp"
    with rio.open(path_tif) as src:
        m_red = src.read(5)
        nir = src.read(7)
        src_nodata = src.nodata
        src_profile = src.profile
    channels = [m_red, nir]
    transform = Transformer()
    segment = Segmenter()
    ndvi = transform.run(channels, src_profile, path_hasil)
    fiturs = [path_tif, ndvi]
    threshold = segment.run(fiturs, src_profile, path_hasil)