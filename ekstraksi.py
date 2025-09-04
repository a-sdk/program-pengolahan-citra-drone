'''
Pustaka untuk mengekstrak fitur citra.
'''

# Libraries
import numpy as np
import rasterio
from rasterio.mask import mask
import geopandas as gpd
import os


def clip_raster_by_mask(input_layer, shapefile_layer):
    """
    Memotong citra sesuai dengan shaepfile poligon yang dibuat.

    Args:
        input_layer (np.ndarray): Data raster yang akan dipotong.
        shapefile_layer (dict): Shapefile yang menjadi acuan.
        
    Returns:
        str: Output path.
    """
    # Tentukan lokasi hasil clip
    output_folder = "Hasil/Clip"
    output_file = "1.tif"
    output_path = os.path.join(output_folder, output_file)
    # Pastikan folder output ada, jika tidak, buat folder baru
    os.makedirs(output_folder, exist_ok=True)
    # Baca Shapefile Menggunakan GeoPandas
    print("Membaca shapefile...")
    mask_gdf = gpd.read_file(shapefile_layer)
    # Operasi clip
    print("Melakukan clipping raster...")
    with rasterio.open(input_layer) as src:
        # Dapatkan geometri dari GeoDataFrame dalam format yang dibutuhkan oleh rasterio
        geometries = mask_gdf.geometry
        # Lakukan masking
        # crop=True akan memotong raster sesuai extent/bounding box dari mask
        out_image, out_transform = mask(src, geometries, crop=True)
        # Salin metadata dari raster asli
        out_meta = src.meta.copy()
    # Perbarui metadata dengan informasi dari hasil clip
    out_meta.update({
        "driver": "GTiff",
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform
    })
    print("Menyimpan hasil clipping...")
    with rasterio.open(output_path, "w", **out_meta) as dest:
        dest.write(out_image)
    print(f"File {output_file} berhasil disimpan di {output_folder}")
    return output_path

# Fungsi untuk melakukan masking
def mask_raster(input_raster, mask_array, nodata_value=-9999):
    """
    Menerapkan masking pada array berdasarkan mask boolean.
    
    Args:
        input_raster (np.ndarray): Array NumPy yang akan di-mask.
        mask_array (np.ndarray): Mask boolean.
        nodata_value (numeric): Nilai piksel yang di-mask.
    
    Returns:
        np.ndarray: Array hasil masking.
    """
    hasil = np.full(input_raster.shape, nodata_value, dtype=np.float32)
    hasil[mask_array] = input_raster[mask_array]
    return hasil