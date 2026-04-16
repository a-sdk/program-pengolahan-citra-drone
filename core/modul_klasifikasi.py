import rasterio as rio
import os
import numpy as np
import logging
import geopandas as gpd
import pandas as pd

logger = logging.getLogger(__name__)

def pisahkan_gulma(model_path, stack_path, output_folder, output_filename, check_cancel, on_progress):
    """
    Menerapkan model terlatih ke seluruh tumpukan fitur untuk memisahkan padi dan gulma.

    Parameters:
        model_path (str): Lokasi model deteksi gulma.
        stack_path (str): Lokasi tumpukan fitur.
        output_folder (str): Nama folder tempat file akan disimpan.
        output_filename (str): Nama file output, termasuk ekstensi. 

    Returns:
        str: Output path.
    """
    import joblib
    output_path = os.path.join(output_folder, output_filename)
    os.makedirs(output_folder, exist_ok=True)
    print(f"Memuat model...")
    try:
        model = joblib.load(model_path)
    except FileNotFoundError:
        print(f"ERROR: File model tidak ditemukan. Silahkan dicek dulu.")
        return

    print(f"Membuka tumpukan fitur...")
    with rio.open(stack_path) as src:
        # Dapatkan metadata untuk file output
        profile = src.profile
        nodata = src.nodata
        profile.update(
            dtype=rio.uint8,  
            count=1,               
            nodata=0           
        )
        
        print(f"Memisahkan padi dengan gulma...")
        with rio.open(output_path, "w", **profile) as dest:
            # Proses citra dalam "potongan" (chunks/tiles) untuk menghemat RAM
            total_blocks = len(list(src.block_windows(1)))
            current_block = 0
            for ji, window in src.block_windows(1):
                current_block += 1
                # Memeriksa interupsi
                if check_cancel and check_cancel():
                    logger.warning("Segmenter dihentikan")
                    return None
                
                # Perbarui progres internal 
                if on_progress and current_block % 10 == 0:
                    relative_prog = 40 + int((current_block/total_blocks) * 10)
                    on_progress(relative_prog, f"Separating vegetation ({current_block}/{total_blocks})...")
                # Baca data untuk potongan ini
                stack_chunk = src.read(window=window)
                
                # Reshape 3D (bands, rows, cols) -> 2D (pixels, features)
                # Pindahkan sumbu bands ke akhir: (rows, cols, bands)
                img_reshaped = np.moveaxis(stack_chunk, 0, -1)
                # Ratakan: (rows*cols, bands)
                pixels_flat = img_reshaped.reshape(-1, src.count)
                
                # Cari piksel yang valid (bukan NoData)
                valid_mask = pixels_flat[:, 6] != nodata
                pixels_valid = pixels_flat[valid_mask]
                
                # Siapkan kanvas hasil untuk potongan ini
                result_chunk = np.zeros(pixels_flat.shape[0], dtype=rio.uint8)
                
                # Lakukan Prediksi (Hanya pada piksel valid)
                if pixels_valid.shape[0] > 0:
                    predictions = model.predict(pixels_valid)
                    
                    # Isi kanvas hasil
                    result_chunk[valid_mask] = predictions
                
                # Bentuk kembali 1D -> 2D dan tulis ke file output
                result_chunk_2d = result_chunk.reshape(window.height, window.width)
                dest.write(result_chunk_2d.astype(rio.uint8), window=window, indexes=1)
                
    print(f"Pemisahan selesai! Peta segmentasi disimpan di: {output_folder}")
    return output_path

class PlantDiseaseClassifier:
    """
    Kelas untuk deteksi penyakit per rumpun.
    """ 
    def __init__(self):
        self.status = "Idle"
        self.last_result = None
        self.scaler = None
        self.model = None

    def _load_model(self):
        if self.model is not None:
            return
        import tensorflow as tf
        import joblib

        model_path = "core/models/deteksi_penyakit/model_deteksi_penyakit.h5"
        scaler_path = "core/scaler/model_deteksi_penyakit_Scaler.joblib"
        self.scaler = joblib.load(scaler_path)
        logger.info("Memuat scaler")
        self.model = tf.keras.models.load_model(model_path, compile=False)
        logger.info(f"Model dimuat bertipe: {type(self.model)}")

    def run(self, input_folder, output_folder, check_cancel=None, on_progress=None):
        self.status = "Processing"
        logger.info("Memprediksi penyakit...") 
        print("DEBUG: Prediksi penyakit")
        try:
            self.last_result = self.deteksi_penyakit_rumpun(input_folder, output_folder, check_cancel, on_progress) 
            self.status = "Done"
            return self.last_result
        except Exception as e:
            self.status = "Error"
            logger.error(f"ERROR: {e}")
            return None 
          
    def deteksi_penyakit_rumpun(self, input_folder, output_folder, check_cancel, on_progress):
        """
        Menerapkan model multi-output ke raster dan menghasilkan 4 peta sebaran terpisah.

        Parameters:
            input_folder (str): Lokasi folder berisi file GeoTiff. 
            output_folder (str): Nama folder tempat file akan disimpan.

        Returns:
            str: Output path.
        """
        self._load_model()
        
        output_names = ["blas", "hdb", "bercak cokelat", "bercak sempit"] 
        path_hasil = []
        print(f"Memprediksi citra...")
        with rio.open(input_folder) as src:
            base_profile = src.profile
            base_profile.update(
                dtype=rio.uint8, 
                count=1,          
                nodata=0
            )
            output_dests = {}
            output_folder = f"{output_folder}/Hasil_Prediksi/Sebaran_Rumpun"
            os.makedirs(output_folder, exist_ok=True)
            for i, name in enumerate(output_names):
                output_path = os.path.join(output_folder, f"peta_sebaran_penyakit_{name}.tif")
                path_hasil.append(output_path)
                output_profile = base_profile.copy()
                if os.path.exists(output_path):
                    output_dests[name] = rio.open(output_path, 'r+')
                else:
                    output_dests[name] = rio.open(output_path, 'w', **output_profile)
            total_blocks = len(list(src.block_windows(1)))
            current_block = 0
            # Memproses lewat potongan (chunk)
            for ji, window in src.block_windows(1):
                current_block += 1
                # Memeriksa interupsi
                if check_cancel and check_cancel():
                    logger.warning("Classifier dihentikan")
                    return None
                
                # Perbarui progres internal 
                if on_progress and current_block % 10 == 0:
                    relative_prog = 70 + int((current_block/total_blocks) * 20)
                    on_progress(relative_prog, f"Generating prediction ({current_block}/{total_blocks})...")
                
                # print(f"Memproses potongan di {window}...")
                
                # Baca per potongan
                stack_chunk = src.read(window=window)
                
                # Reshape (bands, rows, cols) -> (pixels, features)
                img_reshaped = np.moveaxis(stack_chunk, 0, -1)
                pixels_flat = img_reshaped.reshape(-1, src.count)
                
                # Menentukan piksel yang valid
                valid_mask = (pixels_flat[:, 0] != src.nodata)
                pixels_valid = pixels_flat[valid_mask]
                
                # Memprediksi piksel 
                if pixels_valid.shape[0] > 0:
                    pixels_valid_scaled = self.scaler.transform(pixels_valid)
                    predictions_list = self.model.predict(pixels_valid_scaled, verbose=0)
                else:
                    predictions_list = [np.array([])] * len(output_names) 

                # Loop setiap output
                for i, name in enumerate(output_names):
                    
                    result_chunk = np.zeros(pixels_flat.shape[0], dtype=rio.uint8)
                    
                    if predictions_list[i].size > 0:
                        labels_kelas = predictions_list[i].argmax(axis=1) 
                        
                        result_chunk[valid_mask] = labels_kelas + 1 
                    
                    # Reshape 1D -> 2D
                    result_chunk_2d = result_chunk.reshape(window.height, window.width)
                    
                    # Menyimpan hasil prediksi
                    dest = output_dests[name]
                    dest.write(result_chunk_2d, window=window, indexes=1)
                    
            # Menutup semua file output setelah loop selesai
            for dest in output_dests.values():
                dest.close()
                    
        print(f"\nDeteksi selesai! 4 peta disimpan di folder: {output_folder}")
        return path_hasil

class PlotDiseaseClassifier:
    """
    Kelas untuk deteksi penyakit per plot/petak.
    """ 
    def __init__(self):
        self.status = "Idle"
        self.last_result = None

    def run(self, model_path, scaler_path, input_folder, shp_path, output_folder):
        self.status = "Processing"
        logger.info("Memprediksi penyakit...") 
        try:
            self.last_result = self.deteksi_penyakit_petak(model_path, scaler_path, input_folder, shp_path, output_folder) 
            self.status = "Done"
            return self.last_result
        except Exception as e:
            self.status = "Error"
            logger.error(f"ERROR: {e}")
            return None 
        
    def deteksi_penyakit_petak(self, input_folder, shp_path, output_folder):
        """
        Menerapkan model multi-output ke untuk memprediksi
        penyakit dari dataset.

        Parameters:
            input_folder (str): Lokasi folder hasil ekstraksi nilai piksel.
            shp_path (str): Lokasi shapefile yang menjadi acuan.
            output_folder (str): Nama folder tempat file akan disimpan.

        Returns:
            str: Output path.
        """

        df = pd.read_csv(input_folder)
        gdf = gpd.read_file(shp_path)

        fitur = ["RED", "GREEN", "BLUE", "M_GREEN", "M_RED", "RED_EDGE", "NIR"]
        X_inf = df[fitur]
        X_inf_array = X_inf.values
        print("Menormalisasi data...")
        X_inf_scaled = self.scaler_disease.transform(X_inf_array)
        print("Memprediksi penyakit...")
        raw_preds = self.model_disease.predict(X_inf_scaled)

        map_label = {1: "Sehat", 2: "Ringan", 3: "Sedang", 4: "Parah"}
        disease_names = ["blas", "blb", "bs", "nbs"]

        for i, name in enumerate(disease_names):
            # Ambil index kelas tertinggi
            class_idx = np.argmax(raw_preds[i], axis=1) + 1
            # Masukkan ke dataframe
            df[f"Prediksi_{name}"] = [map_label[idx] for idx in class_idx]
            gdf[name] = [idx for idx in class_idx]

        output_folder = f"{output_folder}/Sebaran_Petak"
        os.makedirs(output_folder, exist_ok=True)
        output_path = os.path.join(output_folder, "Hasil_Prediksi.xlsx")
        output_shp = os.path.join(output_folder, "Hasil_Prediksi.shp")
        print(f"Menyimpan hasil prediksi di {output_folder}")
        df.to_excel(output_path, index=False)
        gdf.to_file(output_shp, driver="ESRI Shapefile")
        
        return output_shp, disease_names

