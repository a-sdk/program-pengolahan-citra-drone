'''
Modul berisi fungsi-fungsi pembantu
yang digunakan pada program utama
'''
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import rasterio as rio

# Fungsi untuk meminta folder path
def ambil_file(ekstensi):
    """
    Mengambil file dengan ekstensi tertentu
    dalam suatu folder berdasarkan input.

    Args:
        ekstensi (str): Ekstensi file yang diambil.

    Returns:
        list: File target dan lokasi folder
    """
    while True:
        lokasi_folder = input(f"\nMasukkan path folder berisi file {ekstensi}: ").strip('"').strip("'")
        if  not os.path.isdir(lokasi_folder):
            print(f"Folder tidak ditemukan: {lokasi_folder}")
            print("Silahkan dicek dahulu.")
            continue
        folder_target = os.path.join(lokasi_folder, f"*{ekstensi}")
        file_target = glob.glob(folder_target)
        if not file_target:
            print(f"Tidak ada file {ekstensi} ditemukan di folder tersebut.")
            print("Silahkan dicek dahulu.")
        else:
            print(f"Ditemukan {len(file_target)} file {ekstensi} di folder {lokasi_folder}")
            # Menampilkan file dalam folder 
            print(f"Daftar File '{ekstensi}' dalam Folder {lokasi_folder}")
            c = 1
            for files in file_target:
                nf = os.path.splitext(os.path.basename(files))[0]
                print(f"\t {c}) {nf}")
                c += 1
            return file_target, lokasi_folder

# Fungsi untuk memeriksa ukuran raster
def cek_ukuran_raster(input_raster):
    """
    Menghitung ukuran raster dan menampilkannya di terminal/shell.

    Args:
        input_raster (np.ndarray): Array NumPy yang akan dihitung.
        
    Returns:
        None.
    """
    nf = os.path.basename(input_raster)
    with rio.open(input_raster) as src:
        print(f"Memeriksa bentuk...")
        band1 = src.read()
        print(f"Bentuk (shape) dari {nf} adalah {band1.shape}")

# Fungsi untuk menyimpan array NumPy ke dalam file GeoTIFF
def simpan_raster(input_raster, profile, output_folder, output_filename, nilai_nodata=None):
    """
    Menyimpan array NumPy sebagai file GeoTIFF ke folder yang ditentukan.

    Args:
        input_raster (np.ndarray): Array NumPy yang akan disimpan.
        profile (dict): Metadata raster dari file sumber.
        output_folder (str): Nama folder tempat file akan disimpan.
        output_filename (str): Nama file output, termasuk ekstensi.
        
    Returns:
        str: Output path.
    """
    # Gabungkan nama folder dan nama file
    output_path = os.path.join(output_folder, output_filename)

    # Pastikan folder output ada, jika tidak, buat folder baru
    os.makedirs(output_folder, exist_ok=True)

    # Perbarui profil untuk file output
    profile.update(
        dtype=input_raster.dtype,  
        count=1,
        driver="GTiff"
    )
    if nilai_nodata is not None:
        profile.update(nodata=nilai_nodata)
        
    with rio.open(output_path, 'w', **profile) as dest:
        dest.write(input_raster, 1)

    print(f"File {output_filename} berhasil disimpan di {output_folder}")
    return output_path

# Fungsi untuk menentukan threshold secara otomatis
def otsu_threshold(input_raster, jumlah_bin=256, rentang_nilai=(-1, 1)):
    """
    Menghitung threshold untuk masking raster.

    Args:
        input_raster (np.ndarray): Data raster yang akan dihitung thresholdnya.
        jumlah_bin (int): Jumlah bin histogram.
        rentang_nilai (str): Nilai min dan max yang ada pada data raster.
        
    Returns:
        float: Nilai threshold.
    """
    # Histogram dan probabilitas
    hist, bin_edges = np.histogram(input_raster.ravel(), bins=jumlah_bin, range=rentang_nilai)
    prob = hist.astype(float) / hist.sum()

    # Bin center
    bin_mids = (bin_edges[:-1] + bin_edges[1:]) / 2

    # Probabilitas kumulatif (q1) dan mean kumulatif (mu1)
    q1 = np.cumsum(prob)
    mu1 = np.cumsum(prob * bin_mids)

    # Total mean
    global_mean = mu1[-1]

    # Kelas 2
    q2 = 1 - q1
    mu2 = global_mean - mu1

    # Hindari pembagian dengan nol
    valid = (q1 > 0) & (q2 > 0)

    mean1 = np.zeros_like(mu1)
    mean2 = np.zeros_like(mu1)

    mean1[valid] = mu1[valid] / q1[valid]
    mean2[valid] = mu2[valid] / q2[valid]

    # Variansi antar kelas
    selisih_var = q1 * q2 * (mean1 - mean2) ** 2

    # Ambil threshold dengan variansi antar kelas maksimum
    nilai_terbaik = np.argmax(selisih_var * valid) 
    threshold = bin_mids[nilai_terbaik]

    return threshold

# Fungsi menampilkan histogram 
def tampilkan_histogram(nama, data, nilai_threshold):
    """
    Menampilkan histogram dari hasil perhitungan transformasi indeks vegetasi.

    Args:
        nama (str): Nama transformasi indeks vegetasi yang digunakan.
        data (np.ndarray): Array NumPy yang akan ditampilkan.
        nilai_threshold (float): Batas yang ditentukan.
        
    Returns:
        None.
    """
    # Membuat histogram untuk menampilkan data piksel SAVI
    print(f"Menampilkan histogram {nama}...")
    plt.figure(figsize=(10, 6))
    plt.hist(data, bins=100, color='lightgreen', edgecolor='black')
    plt.title(f"Histogram Nilai {nama}")
    plt.xlabel(f"Nilai {nama}")
    plt.ylabel("Frekuensi Piksel")
    plt.grid(True, alpha=0.5)
    plt.axvline(x=nilai_threshold, color='r', linestyle='--', label=f"Batas = {nilai_threshold}")
    plt.legend()
    plt.show()

# Fungsi menumpuk semua fitur (band)
def tumpuk_fitur(lst_fitur, output_folder, output_filename):
    """
    Menumpuk seluruh band atau fitur menjadi array Numpy besar.

    Args:
        lst_fitur (list): List fitur-fitur yang akan ditumpuk.
        output_folder (str): Nama folder tempat file akan disimpan.
        output_filename (str): Nama file output, termasuk ekstensi.

    Returns:
        str: Output path.
    """
    # Gabung nama folder dan file
    output_path = os.path.join(output_folder, output_filename)
    os.makedirs(output_folder, exist_ok=True)
    # Baca semua file dan kumpulkan datanya
    feature_stack = []
    profile = None # Kita akan ambil metadata dari file pertama

    for fitur in lst_fitur:
        with rio.open(fitur) as src:
            if profile is None:
                profile = src.profile
            
            # Baca semua band dari file ini
            feature_stack.append(src.read())

    # Gabungkan semua data menjadi satu array NumPy besar
    full_stack_array = np.vstack(feature_stack)

    # Perbarui profile untuk file stack baru
    total_bands = full_stack_array.shape[0]
    profile.update(count=total_bands, nodata=np.nan) 

    # Tulis ke file stack baru
    with rio.open(output_path, 'w', **profile) as dst:
        dst.write(full_stack_array)

    print(f"Tumpukan fitur berhasil disimpan di: {output_folder}")
    return output_path
