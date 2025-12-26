'''
Modul berisi fungsi-fungsi pembantu
yang digunakan pada program utama
'''
import os
import glob
import numpy as np
import pandas as pd
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

# Fungsi untuk mengolah label penyakit 
def olah_label(input_folder, output_folder, N, z):
    """
    Mengolah label skor penyakit hasil pengamatan
    untuk memperoleh intensitas penyakit dan indeks penyakit.
    Pastikan nama file label seperti contoh "hst 50.csv"

    Args:
        input_folder (str): Lokasi folder skor penyakit.
        output_folder (str): Nama folder tempat file akan disimpan.
        N (int): Jumlah rumpun yang diamati.
        z (int): Skala maksimal skor penyakit.

    Returns:
        None.
    """
    files = glob.glob(os.path.join(input_folder, "*.csv"))
    for file in files:
        nf = os.path.splitext(os.path.basename(file))[0]
        print(f"\nMemproses file {nf}...")
        umur = nf.split(r" ")[1]
        # Membaca setiap file
        df = pd.read_csv(file)
        grup = df.groupby("id") 
        lst_skor = []

        print("Menghitung intensitas penyakit...")
        for id_titik, data in grup:
            baris = {"id": id_titik, "hst": umur}
            penyakit_dict = {
                "blas": data["blas"],
                "blb": data["blb"],
                "bs": data["bs"],
                "nbs": data["nbs"]
            }
            for nama_penyakit, penyakit in penyakit_dict.items():
                skor = penyakit.value_counts(dropna=False)
                skor_max = penyakit.max() # Nilai maks sbg worst case
                skor_mode = penyakit.mode(dropna=False).iloc[0] # Nilai modus sebagai gambaran umum
                n1 = skor.get(1,0)
                n3 = skor.get(3,0)
                n5 = skor.get(5,0)
                n7 = skor.get(7,0)
                n9 = skor.get(9,0)
                sum_nv = n1 * 1 + n3 * 3 + n5 * 5 + n7 * 7 + n9 * 9
                hitung_ip = round((sum_nv / (N * z)) * 100, 2)
                hitung_di = round((n3 + n5 + n7 + n9) / N, 2)
                # Nilai berdasarkan intensitas penyakit
                if hitung_ip == 0:
                    status = "sehat"
                elif 0 < hitung_ip <= 30:
                    status = "ringan"
                elif 30 < hitung_ip <= 50:
                    status = "agak parah"
                else:
                    status = "parah"
                # Nilai berdasarkan disease index (DI)
                if hitung_di == 0:
                    idx = "sehat"
                elif 0 < hitung_di <= 3:
                    idx = "tahan"
                elif 3 < hitung_di <= 6:
                    idx = "rentan"
                else: 
                    idx = "sangat rentan"
                baris[f"{nama_penyakit}"] = status
                baris[f"{nama_penyakit}_ip"] = hitung_ip
                baris[f"{nama_penyakit}_di"] = idx
                print(f"Titik {id_titik} - DI {nama_penyakit}: {idx} ({hitung_di})")
                print(f"Titik {id_titik} - IP {nama_penyakit}: {hitung_ip:.2f} %, status={status}")
                print(f"Titik {id_titik} - Skor Terparah {nama_penyakit}: {skor_max}")
                print(f"Titik {id_titik} - Skor Umum {nama_penyakit}: {skor_mode}")
                
            lst_skor.append(baris)
            print()

        df_hasil = pd.DataFrame(lst_skor)
        lst_kolom = [
            "id",
            "hst",
            "blas",
            "blb",
            "bs",
            "nbs",
            "blas_ip",
            "blb_ip",
            "bs_ip",
            "nbs_ip",
            "blas_di",
            "blb_di",
            "bs_di",
            "nbs_di"
        ]
        # Menyimpan file ke csv
        print(f"Menyimpan _{nf}.csv")
        df_hasil = df_hasil[lst_kolom]
        df_hasil.to_csv(rf"{output_folder}\_{nf}.csv", index=False) 
        print(f"Selesai memproses {len(files)} file .csv")

# Fungsi untuk menggabungkan label penyakit
def gabung_label(input_folder, output_folder, output_filename):
    """
    Menggabungkan beberapa file .csv hasil olah label
    menjadi satu file .csv
    
    Args:
        input_folder (str): Lokasi file label masing-masing HST.
        output_folder (str): Nama folder tempat file akan disimpan.
        output_filename (str): Nama file output, termasuk ekstensi.

    Returns:
        None.
    """
    print("Menggabungkan semua label penyakit...")
    files = glob.glob(os.path.join(input_folder, "*.csv"))
    labels = []
    c = 1
    for file in files:
        nf = os.path.splitext(os.path.basename(file))[0]
        print(f"\t {c}. {nf}")
        c += 1
        umur = nf.split(r" ")[1]
        df_label = pd.read_csv(file)
        df_label["hst"] = umur
        labels.append(df_label)

    label_hasil = pd.concat(labels, axis=0, ignore_index=True)
    output_path = os.path.join(output_folder, output_filename)
    os.makedirs(output_folder, exist_ok=True)
    label_hasil.to_csv(output_path, index=False)
    print(f"File {output_filename} berhasl disimpan di: \n{output_folder}")

# Fungsi untuk menggabungkan dataset dan label
def olah_dataset(dataset_folder, label_folder, output_folder, output_filename):
    """
    Menggabungkan file dataset dengan label
    
    Args:
        dataset_folder (str): Lokasi folder dataset.
        label_file (str): Lokasi file gabungan label. 
        output_folder (str): Nama folder tempat file akan disimpan.
        output_filename (str): Nama file output, termasuk ekstensi.

    Returns:
        None.
    """
    files_ekstraksi = glob.glob(os.path.join(dataset_folder, "*.csv"))
    output_path = os.path.join(output_folder, output_filename)
    os.makedirs(output_folder, exist_ok=True)
    # Membaca file ke dataframe dan menambah kolom hst
    print("Membaca file hasil ekstraksi...")
    df0 = pd.read_csv(files_ekstraksi[0])
    df1 = pd.read_csv(files_ekstraksi[1])
    df2 = pd.read_csv(files_ekstraksi[2])
    df3 = pd.read_csv(files_ekstraksi[3])
    df4 = pd.read_csv(files_ekstraksi[4])
    df5 = pd.read_csv(files_ekstraksi[5])

    df0["hst"] = 40
    df1["hst"] = 40
    df2["hst"] = 30
    df3["hst"] = 45
    df4["hst"] = 45
    df5["hst"] = 60

    # Menggabungkan semua file hasil ekstraksi
    lst_df = [df0, df1, df2, df3, df4, df5]
    df = pd.concat(lst_df, axis=0)
    df_label = pd.read_csv(label_folder)
    # Menggabungkan data dengan label
    print("Menambahkan label...")
    df_lengkap = df.merge(df_label, on=["id", "hst"])
    kolom_umur = df_lengkap.pop("hst")

    df_lengkap = df_lengkap.drop(columns=["blas_ip", "blb_ip", "bs_ip", "nbs_ip", 
                                          "blas_di", "blb_di", "bs_di", "nbs_di"])
    df_lengkap.insert(loc=2, column="HST", value=kolom_umur)
    df_lengkap.rename(columns={"id": "ID"}, inplace=True)
    print("Menyimpan dataset...")
    print(f"File {output_filename} disimpan di:\n{output_folder}")
    df_lengkap.to_csv(output_path, index=False)

if __name__ == "__main__":
    folder_dataset = r"C:\Users\acer_\Documents\Hasil_Ekstraksi\rev1"
    file_label = r"C:\Users\acer_\Documents\Hasil_Ekstraksi\labels\gabungan\_label_final.csv"
    folder_hasil = r"C:\Users\acer_\Documents\Hasil_Ekstraksi\rev1\dataset"
    nf_hasil = "dataset_lengkap_rerata_piksel_rev2.csv"
    olah_dataset(folder_dataset, file_label, folder_hasil, nf_hasil)