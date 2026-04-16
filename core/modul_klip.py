"""
Modul untuk memotong citra.
"""

import os
import geopandas as gpd
import rasterio as rio
from rasterio.mask import mask
import logging

logger = logging.getLogger(__name__)

class Clipper:
    """
    Kelas untuk memotong citra.
    """
    def __init__(self):
        self.status = "Idle"
        self.last_result = None

    def run(self, input_folder, shp_path, output_folder):
        self.status = "Processing"
        logger.info("Memulai clipping...") 
        try:
            self.last_result = self.potong_raster(input_folder, shp_path, output_folder) 
            self.status = "Done"
            return self.last_result
        except Exception as e:
            self.status = "Error"
            logger.error(f"ERROR {type(e).__name__}: {e}", exc_info=True)
            return None
    
    # Fungsi untuk memotong citra bedasarkan shapefile poligon
    def potong_raster(self, input_folder, shp_path, output_folder, output_filename="hasil_potong.tif", nilai_nodata=0):
        """
        Memotong citra sesuai dengan shapefile poligon yang dibuat.

        Parameters:
            input_folder (str): Lokasi file raster yang akan dipotong.
            shp_path (str): Lokasi shapefile yang menjadi acuan.
            output_folder (str): Nama folder tempat hasil klip disimpan.
            output_filename (str): Nama file output, termasuk ekstensi
            
        Returns:
            str: Output path.
        """
        # Tentukan lokasi hasil clip
        output_path = os.path.join(output_folder, output_filename)
        # Pastikan folder output ada, jika tidak, buat folder baru
        os.makedirs(output_folder, exist_ok=True)
        # Baca Shapefile Menggunakan GeoPandas
        print("\nMemuat shapefile...")
        mask_gdf = gpd.read_file(shp_path)
        print("Memuat citra...")
        with rio.open(input_folder) as src:
            profile = src.profile
            geometries = mask_gdf.geometry
            # Melakukan masking
            print("Memotong raster berdasarkan shapefile...")
            out_image, out_transform = mask(
                src,
                geometries, 
                crop=True,
                filled=True,
                nodata=nilai_nodata
                )
        # Perbarui metadata dengan informasi dari hasil clip
        profile.update(
            dtype="uint16",
            height=out_image.shape[1],
            width=out_image.shape[2],
            count=out_image.shape[0],
            transform=out_transform,
            BIGTIFF="YES",
            nodata=nilai_nodata,
            driver="GTiff"
        )
        print("Menyimpan hasil clipping...")
        with rio.open(output_path, "w", **profile) as dest:
            dest.write(out_image)
        print(f"File {output_filename} berhasil disimpan di {output_folder}")
        return output_path
    
if __name__ == "__main__":
    path_hasil = r"C:\Users\acer_\Documents\Orthomosaic\tes program skripsi\klip"
    path_tif = r"C:\Users\acer_\Documents\Orthomosaic\tes program skripsi\HST 29 36_PAGI_30.tif"
    path_poly = r"C:\Users\acer_\Documents\Shapefiles\cikembar\Lahan 2_0.shp"
    test = Clipper()
    hasil = test.run(path_tif, path_poly, path_hasil)