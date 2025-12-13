import rasterio as rio
import os
import numpy as np
import joblib
import tensorflow as tf
import glob
def pisahkan_gulma(model_path, stack_path, output_folder, output_filename, nilai_nodata=np.nan):
    """
    Menerapkan model terlatih ke seluruh tumpukan fitur untuk memisahkan padi dan gulma.

    Args:
        model_path (str): Lokasi model klasifikasi.
        stack_path (str): Lokasi tumpukan fitur.
        output_folder (str): Nama folder tempat file akan disimpan.
        output_filename (str): Nama file output, termasuk ekstensi. 
        nilai_nodata (float): Nilai nodata.

    Returns:
        str: Output path.
    """
    output_path = os.path.join(output_folder, output_filename)
    os.makedirs(output_folder, exist_ok=True)
    print(f"Memuat model dari {model_path}...")
    try:
        model = joblib.load(model_path)
    except FileNotFoundError:
        print(f"ERROR: File model tidak ditemukan. Silahkan dicek dulu.")
        return

    print(f"Membuka tumpukan fitur...")
    with rio.open(stack_path) as src:
        # Dapatkan metadata untuk file output
        profile = src.profile
        profile.update(
            dtype=rio.uint8,  
            count=1,               
            nodata=0            
        )
        
        print(f"Memisahkan padi dengan gulma...")
        with rio.open(output_path, "w", **profile) as dest:
            
            # Proses citra dalam "potongan" (chunks/tiles) untuk menghemat RAM
            for ji, window in src.block_windows(1):
                
                # Baca data untuk potongan ini
                stack_chunk = src.read(window=window)
                
                # Reshape 3D (bands, rows, cols) -> 2D (pixels, features)
                # Pindahkan sumbu bands ke akhir: (rows, cols, bands)
                img_reshaped = np.moveaxis(stack_chunk, 0, -1)
                # Ratakan: (rows*cols, bands)
                pixels_flat = img_reshaped.reshape(-1, src.count)
                
                # Cari piksel yang valid (bukan NoData di band pertama)
                valid_mask = ~np.isnan(pixels_flat[:, 0])
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
                
    print(f"Klasifikasi selesai! Peta segmentasi disimpan di: {output_folder}")
    return output_path

def deteksi_penyakit_padi(model_path, scaler_path, input_folder, output_folder):
    """
    Menerapkan model multi-output ke raster dan menghasilkan 4 peta klasifikasi terpisah.

    Args:
        model_path (str): Lokasi model klasifikasi.
        input_folder (str): Lokasi raster.
        output_folder (str): Nama folder tempat file akan disimpan.
        output_filename (str): Nama file output, termasuk ekstensi. 
        nilai_nodata (float): Nilai nodata.

    Returns:
        str: Output path.
    """
    file_raster = glob.glob(os.path.join(input_folder, "*tif"))
    print(f"Memuat model dari {model_path}...")
    print(f"Memuat scaler dari {scaler_path}...")
    try:
        model = tf.keras.models.load_model(model_path) 
        scaler_loaded = joblib.load(scaler_path)
    except Exception as e:
        print(f"ERROR: Gagal memuat: {e}")
        return

    output_names = ["BLAS", "BLB", "BS", "NBS"] 

    print(f"Memprediksi citra...")
    with rio.open(file_raster[0]) as src:
        base_profile = src.profile
        base_profile.update(
            dtype=rio.float32, 
            count=1,          
            nodata=src.nodata
        )
        output_dests = {}
        for name in output_names:
            output_path = os.path.join(output_folder, f"peta_klasifikasi_{name}.tif")
            os.makedirs(output_folder, exist_ok=True)
            
            output_profile = base_profile.copy()
            mode = 'r+' if os.path.exists(output_path) else 'w'
            output_dests[name] = rio.open(output_path, mode, **output_profile)

        # Memproses lewat potongan (chunk)
        for ji, window in src.block_windows(1):
            print(f"Memproses potongan di {window}...")
            
            # Baca per potongan
            stack_chunk = src.read(window=window)
            
            # Reshape (bands, rows, cols) -> (pixels, features)
            img_reshaped = np.moveaxis(stack_chunk, 0, -1)
            pixels_flat = img_reshaped.reshape(-1, src.count)
            
            # Menentukan piksel yang valid
            valid_mask = ~np.isnan(pixels_flat[:, 0])
            pixels_valid = pixels_flat[valid_mask]
            
            # Memprediksi piksel 
            if pixels_valid.shape[0] > 0:
                pixels_valid_scaled = scaler_loaded.transform(pixels_valid)
                predictions_list = model.predict(pixels_valid_scaled, verbose=0)
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
                
    print(f"\nKlasifikasi selesai! 4 peta segmentasi disimpan di folder: {output_folder}")
    return