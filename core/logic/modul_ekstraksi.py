'''
Modul untuk ekstraksi fitur citra.
'''

# Libraries
import pandas as pd
import rasterio as rio
from rasterstats import zonal_stats
import geopandas as gpd
import os
import logging

logger = logging.getLogger(__name__)

# Fungsi untuk mengekstrak rata-rata nilai piksel dalam sub poligon
def ekstrak_rerata_piksel(shp_path, input_folder, output_folder, output_filename="pixel_val.csv"):
    """
    Mengekstrak rata-rata piksel dalam poligon dari tumpukan fitur.

    Parameters:
        shp_path (str): Lokasi shapefile yang menjadi acuan.
        input_folder (str): Lokasi file tumpukan fitur.
        output_folder (str): Nama folder tempat file akan disimpan.
        output_filename (str): Nama file output, termasuk ekstensi.

    Returns:
        str: Output path.
    """
    gdf = gpd.read_file(shp_path)

    # Menyiapkan kolom identitas
    # gdf["no_urut"] = gdf.groupby("id").cumcount() + 1
    gdf["Nama"] = "Poligon " + gdf["id"].astype(str) + " Komponen " + gdf["no_urut"].astype(str)
    
    # Mengambil koordinat X dan Y dari centroid poligon
    gdf["X"] = gdf.geometry.centroid.x
    gdf["Y"] = gdf.geometry.centroid.y

    # Menyiapkan DataFrame hasil dengan kolom koordinat awal
    hasil_ekstraksi = gdf[["id", "no_urut", "Nama", "X", "Y"]].copy()
    
    with rio.open(input_folder) as info:
        count = info.count
    

    with rio.open(input_folder) as src:
        count = src.count
        if count > 7:
            nama_bands = [
                "RED", "GREEN", "BLUE", "M_GREEN", "M_RED", 
                "RED_EDGE", "NIR", "GNDVI", "NDREI", "NDVI", "SAVI"
            ]
        else:
            nama_bands = [
                "RED", "GREEN", "BLUE", "M_GREEN", "M_RED", 
                "RED_EDGE", "NIR"
            ]
        for i, name in enumerate(nama_bands):
            band_data = src.read(i + 1)
            
            stats = zonal_stats(
                vectors=gdf, 
                raster=band_data, 
                affine=src.transform, 
                stats=["mean"], 
                nodata=src.nodata,
                all_touched=True # Mengambil semua piksel yang bersentuhan
            )
            
            mean_values = [s.get("mean", src.nodata) for s in stats]
            hasil_ekstraksi[name] = mean_values

    # Cek baris yang mengandung NaN sebelum dihapus
    df_lengkap = pd.DataFrame(hasil_ekstraksi)
    nan_rows = df_lengkap[df_lengkap.isna().any(axis=1)]
    
    if not nan_rows.empty:
        logger.info(f"PERHATIAN: Ditemukan {len(nan_rows)} komponen poligon dengan nilai NaN.")
        # logger.info(f"Poligon yang bermasalah: {nan_rows['Nama'].tolist()}")
    # ------------------------
    # Pembersihan dan pengurutan data
    # print(f"Membersihkan hasil ekstraksi...")
    df = pd.DataFrame(hasil_ekstraksi).dropna()
    df_urut = df.sort_values(by=["id", "no_urut"], ascending=True)
    df_urut = df_urut.drop(columns=["no_urut"])
    # df_urut.rename(columns={"no_urut": "id"}, inplace=True)
    
    # Simpan file
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, output_filename)
    df_urut.to_csv(output_path, index=False)
    
    # print(f"Ekstraksi selesai...")
    # print(f"Total baris yang diekstrak: {df_urut.shape[0]}")
    # print(rf"File {output_filename} berhasil disimpan di {output_folder}")    
    return output_path 


        
             
