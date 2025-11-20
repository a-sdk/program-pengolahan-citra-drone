import rasterio
import os
import numpy as np
import joblib

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
    with rasterio.open(stack_path) as src:
        # Dapatkan metadata untuk file output
        profile = src.profile
        profile.update(
            dtype=rasterio.uint8,  # Kita akan menyimpan label (1, 2, dll)
            count=1,               # Output hanya 1 band
            nodata=0               # Set NoData output ke 0
        )
        
        print(f"Memisahkan padi dengan gulma...")
        with rasterio.open(output_path, "w", **profile) as dest:
            
            # Proses citra dalam "potongan" (chunks/tiles) untuk menghemat RAM
            for ji, window in src.block_windows(1):
                
                # 1. Baca data untuk potongan ini
                stack_chunk = src.read(window=window)
                
                # 2. Reshape 3D (bands, rows, cols) -> 2D (pixels, features)
                # Pindahkan sumbu bands ke akhir: (rows, cols, bands)
                img_reshaped = np.moveaxis(stack_chunk, 0, -1)
                # Ratakan: (rows*cols, bands)
                pixels_flat = img_reshaped.reshape(-1, src.count)
                
                # 3. Handle NoData
                # Cari piksel yang valid (bukan NoData di band pertama)
                valid_mask = pixels_flat[:, 0] != nilai_nodata
                pixels_valid = pixels_flat[valid_mask]
                
                # Siapkan kanvas hasil untuk potongan ini
                result_chunk = np.zeros(pixels_flat.shape[0], dtype=rasterio.uint8)
                
                # 4. Lakukan Prediksi (Hanya pada piksel valid)
                if pixels_valid.shape[0] > 0:
                    predictions = model.predict(pixels_valid)
                    
                    # 5. Isi kanvas hasil
                    result_chunk[valid_mask] = predictions
                
                # 6. Bentuk kembali 1D -> 2D dan tulis ke file output
                result_chunk_2d = result_chunk.reshape(window.height, window.width)
                dest.write(result_chunk_2d.astype(rasterio.uint8), window=window, indexes=1)
                
    print(f"Klasifikasi selesai! Peta segmentasi disimpan di: {output_folder}")
    return output_path
