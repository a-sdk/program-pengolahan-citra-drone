"""
Modul untuk mask citra.
"""

import os
import glob
import numpy as np
import rasterio as rio
import logging

logger = logging.getLogger(__name__)

class Masker:
    """
    Kelas untuk masking citra.
    """
    def __init__(self):
        self.status = "Idle"
        self.last_result = None

    def run(self, input_folder, mask_path, output_folder):
        self.status = "Processing"
        logger.info("Memulai proses masking...") 
        try:
            self.last_result = self.mask_tumpukan_fitur(input_folder, mask_path, output_folder) 
            self.status = "Done"
            return self.last_result
        except Exception as e:
            self.status = "Error"
            logger.error(f"ERROR {type(e).__name__}: {e}", exc_info=True)
            return None
            
    # Fungsi untuk melakukan masking pada setiap band terpisah
    def mask_band_terpisah(self, input_folder, mask_path, output_folder, logika=lambda x: x==1, nilai_nodata=0):
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
        print(f"Mask boolean berhasil dibuat. Total piksel valid: {np.sum(mask_valid)}")
        # Menerapkan mask pada semua file dalam input folder
        lst_file = glob.glob(os.path.join(input_folder, "*.tif"))
        if not lst_file:
            print(f"Tidak ada file .tif di {input_folder}")
        os.makedirs(output_folder, exist_ok=True)
        print(f"Menerapkan mask ke {len(lst_file)} band")
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
    def mask_tumpukan_fitur(self, input_folder, mask_path, output_folder, logika=lambda x: x==1, nilai_nodata=0):
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
        print(f"Mask boolean berhasil dibuat. Total piksel valid: {np.sum(mask_valid)}")
        print(f"Membuka tumpukan fitur...")
        nf = os.path.splitext(os.path.basename(input_folder))[0]
        os.makedirs(output_folder, exist_ok=True)
        output_path = os.path.join(output_folder, f"{nf}_masked.tif")
        with rio.open(input_folder) as src_data:
            # Membaca fitur sekaligus
            data_stack = src_data.read()
            profile = src_data.profile
            print("Menerapkan mask ke semua fitur...")
            data_stack[:, ~mask_valid] = nilai_nodata
            
            # Perbarui profile untuk file output agar konsisten
            profile.update(
                dtype="uint16",
                count=data_stack.shape[0], 
                nodata=nilai_nodata
            )
            print("Menyimpan hasil masking...")
            with rio.open(output_path, "w", **profile) as dest:
                dest.write(data_stack)
        print(f"File {nf}_masked.tif berhasil disimpan di {output_folder}")
        return output_path

if __name__ == "__main__":
    from modul_ekstraksi import Extractor
    from modul_utilitas import Splitter
    path_poly = r"C:\Users\acer_\Documents\Shapefiles\cikembar\Lahan 2_0.shp"
    path_multipoly = r"C:\Users\acer_\Documents\Orthomosaic\tes program skripsi\tes main"
    path_hasil = r"C:\Users\acer_\Documents\Orthomosaic\tes program skripsi\hasil_msk2"
    path_tif = r"C:\Users\acer_\Documents\Orthomosaic\tes program skripsi\klip\hasil_potong.tif"
    threshold_path = r"C:\Users\acer_\Documents\Orthomosaic\tes program skripsi\hasil_trf2\hasil_threshold_model.tif"
    split = Splitter()
    mask = Masker()
    extract = Extractor()
    multipoligon = split.run(path_poly, 1, 1500, path_multipoly)
    hasil = mask.run(path_tif, threshold_path, path_hasil)
    ekstrak = extract.run(multipoligon, hasil, path_hasil)
