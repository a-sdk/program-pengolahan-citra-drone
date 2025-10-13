'''
Pustaka untuk memodifikasi ukuran dan mengekstrak fitur citra.
'''

# Libraries
import numpy as np
import rasterio
from rasterio.mask import mask
import geopandas as gpd
import os
from mahotas.polygon import fill_polygon


def clip_raster_by_mask(input_raster, shapefile_layer, output_folder, output_filename):
    """
    Memotong citra sesuai dengan shaepfile poligon yang dibuat.

    Args:
        input_raster (str): Data raster yang akan dipotong.
        shapefile_layer (str): Shapefile yang menjadi acuan.
        output_filename (str): Nama file output, termasuk ekstensi
        
    Returns:
        str: Output path.
    """
    # Tentukan lokasi hasil clip
    output_path = os.path.join(output_folder, output_filename)
    # Pastikan folder output ada, jika tidak, buat folder baru
    os.makedirs(output_folder, exist_ok=True)
    # Baca Shapefile Menggunakan GeoPandas
    print("Membaca shapefile...")
    mask_gdf = gpd.read_file(shapefile_layer)
    # Operasi clip
    print("Melakukan clipping raster...")
    with rasterio.open(input_raster) as src:
        # Dapatkan geometri dari GeoDataFrame dalam format yang dibutuhkan oleh rasterio
        if src.nodata is not None:
            nilai_nodata = src.nodata
        else:
            nilai_nodata = -9999
        geometries = mask_gdf.geometry
        # Melakukan masking
        out_image, out_transform = mask(src, geometries, crop=True)
        out_image = out_image.astype("float32")
        # Ganti nilai NoData di hasil dengan -9999
        if nilai_nodata is not None:
            out_image[out_image == nilai_nodata] = np.nan  # jika sumber punya nodata lama
        out_image[np.isnan(out_image)] = -9999
        # Salin metadata dari raster asli
        out_meta = src.meta.copy()
    # Perbarui metadata dengan informasi dari hasil clip
    out_meta.update({
        "driver": "GTiff",
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform,
        "nodata": -9999,
        "dtype": "float32"
    })
    print("Menyimpan hasil clipping...")
    with rasterio.open(output_path, "w", **out_meta) as dest:
        dest.write(out_image)
    print(f"File {output_filename} berhasil disimpan di {output_folder}")
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

# Fungsi untuk membuat polygon sebagai grid titik
def render(poly):
    """
    Membuat grid titik dari poligon berdasarkan koordinat piksel.
    Mengembalikan daftar semua koordinat piksel (row, col) di dalam poligon.
    """
    xs, ys = zip(*poly)
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    newPoly = [(int(x - minx), int(y - miny)) for (x, y) in poly]
    grid = np.zeros((maxx - minx + 1, maxy - miny + 1), dtype=np.int8)
    fill_polygon(newPoly, grid)
    return [(x + minx, y + miny) for (x, y) in zip(*np.nonzero(grid))]