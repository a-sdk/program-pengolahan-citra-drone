# Program Pengolahan Citra Drone Multispektral

## Deskripsi Proyek

Proyek ini adalah program untuk mengolah citra udara yang ditangkap oleh drone sehingga menghasilkan data dalam bentuk CSV.

## Fitur Utama

1. Memotong citra berdasarkan poligon.
2. Menghitung indeks vegetasi seperti SAVI, NDVI, NDRE, dan lainnya.
3. Melakukan thresholding untuk memisahkan tanaman dan yang bukan tanaman.
4. Melakukan masking untuk menghapus data raster yang bukan berupa tanaman.
5. Memeriksa ukuran raster.


## Panduan Instalasi dan Penggunaan

Ikuti langkah-langkah berikut untuk menjalankan proyek di komputer lokal Anda.

### Persyaratan

Pastikan Anda telah menginstal Python 3.11 di komputer Anda.

### Instalasi

Salin (clone) atau unduh repositori ini ke folder lokal Anda.

Buka terminal atau Command Prompt dan navigasi ke folder proyek.

### Menyiapkan Virtual Environment

Jalankan perintah berikut untuk membuat virtual environment. Ganti `<nama_virtual_environment>` dengan nama yang diinginkan.

    py -m venv <nama_virtual_environment>

### Menginstall Libraries

Jalankan perintah berikut untuk menginstal semua libraries (pustaka) yang diperlukan:

    pip install -r requirements.txt

Catatan: Pastikan `requirements.txt` sudah ada di folder Anda.


### Menjalankan Program

Jalankan perintah berikut di terminal Anda:

    py program.py

Program akan berjalan dan menunjukkan status proses yang dilakukan.


## Struktur Proyek

    /program_pengolahan_citra_drone
    ├── /Bahan/                     # File-file citra berformat `.tif`
    │   └──Citra.tif                # Contoh file citra yang akan diproses
    ├── /Shapefiles/                # File-file titik, garis, poligon
    │   └── Poligon.shp             # Contoh file poligon untuk acuan ekstraksi
    ├── ekstraksi.py                # Program ekstrasi fitur citra.
    ├── program.py                  # Program utama.
    ├── program_arogansi.py         # Program untuk keperluan percobaan.
    └── transformasi.py             # Program transformasi indeks vegetasi.


---

## Changelogs
### Versi 1.4 - 11 Oktober 2025
* **Fitur Baru**:
    * Menambahkan fitur supaya pengguna dapat menentukan folder kerja di luar folder proyek ini.
    * Memodifikasi penamaan file hasil proses supaya menyesuaikan dengan nama file yang diproses.
    * Membuat file `program_arogansi.py` untuk eksperimen batch file processing.

### Versi 1.3 - 8 Oktober 2025
* **Fitur Baru**:
    * Menambahkan fitur input supaya pengguna dapat memilih file yang diproses.
    * Memodifikasi fungsi menyimpan raster sehingga tidak menimpa file sebelumnya.
    * Menambahkan fitur auto-thresholding berdasarkan citra SAVI.
* **Perbaikan Bug**:
    * Memperbaiki bug pada fungsi transformasi SAVI.
    
### Versi 1.2 - 9 September 2025
* **Fitur Baru**:
    * Menambahkan fungsi clip raster dari shapefile poligon.
    * Melakukan masking pada seluruh kanal multispektral.
    * Menambahkan fungsi untuk memeriksa ukuran raster.


### Versi 1.1 - 7 Agustus 2025        
* **Fitur Baru**:
    * Menambahkan fungsi untuk menyimpan raster.
    * Menambahkan fungsi untuk menampilkan raster pada histogram.
    * Menambahkan fungsi untuk melakukan thresholding.
    * Menambahkan fungsi untuk melakukan masking.
* **Perbaikan Bug**:
    * Memperbaiki bug di mana perhitungan indeks vegetasi tidak akurat.


### Versi 1.0 - 6 Agustus 2025

* Rilis awal program pengolahan citra drone.
* Fungsi dasar untuk membaca band citra.
* Fungsi dasar untuk menghitung indeks vegetasi.
