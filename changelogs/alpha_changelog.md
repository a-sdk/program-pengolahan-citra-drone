# Changelogs

## Alpha version changelogs
### Versi 1.4.11 - 31 Januari 2026
* **Perbaikan Bug**:
    * Menghilangkan proses membangun ulang citra berformat `float32`.
    * Mengkombinasikan 7 kanal spektral dan 4 hasil transformasi dengan workflow lebih efisien

### Versi 1.4.10 - 22 Januari 2026
* **Fitur Baru**:
    * Menambahkan fungsi untuk mengekstrak koordinat vertek di `ekstraksi.py`.
    * Menambahkan kolom koordinat X (longitude) dan Y (latitude) pada fungsi ekstraksi piksel.
    * Menambahkan fungsi untuk membuat multipoligon.
    * Menambahkan fungsi untuk mengekstrak koordinat verteks.
    * Menambahkan fungsi untuk membuat petak sebaran penyakit.

### Versi 1.4.9 - 26 Desember 2025
* **Fitur Baru**:
    * Menambahkan fungsi untuk mengolah label dan dataset di `utils.py`.
* **Perbaikan Bug**:
    * Memperbaiki kesalahan nilai nodata pada `klasifikasi.py`. 
    * Memperbaiki kesalahan urutan komponen hasil ekstraksi pada fungsi `ekstrak_rerata_piksel()`.

### Versi 1.4.8 - 13 Desember 2025
* **Fitur Baru**:
    * Membuat fungsi untuk mendeteksi penyakit tanaman padi.
    * Membuat versi pertama untuk program deteksi penyakit di `deteksi.py`.
* **Perbaikan Bug**:
    * Memperbaiki kebocoran memori pada fungsi `clip_raster()`. 

### Versi 1.4.7 - 20 November 2025
* **Fitur Baru**:
    * Membuat fungsi untuk mengekstrak rata-rata nilai piksel dari multi poligon.
  
### Versi 1.4.6 - 08 November 2025
* **Fitur Baru**:
    * Membuat dukungan untuk melakukan batch processing.
    * Menampilkan waktu terpisah per proses dan waktu keseluruhan.
    * Memodifikasi fungsi `clip_raster()` untuk mendukung operasi BigTIFF.
    
### Versi 1.4.5 - 03 November 2025
* **Fitur Baru**:
    * Membuat dua opsi alur kerja antara fitur terpisah atau tumpukan fitur.
    * Memuat proses ektraksi nilai piksel ke dalam fungsi.
    * Merapikan folder hasil dari masing-masing proses pengolahan.
    * Memindahkan fungsi utilitas ke file `utils.py`.
    * Memisahkan setiap band ke file terpisah beserta hasil transformasi indeks.
    * Memodifikasi fungsi `mask_raster()` menjadi `mask_band_terpisah()` untuk melakukan masking pada file terpisah.
    * Mengubah alur kerja menjadi: 
        clip -> transformasi -> segmentasi -> masking -> ektraksi.
    * Memodifikasi folder hasil dari setiap langkah sesuai dengan perubahan alur kerja.
    * Memodifikasi fungsi masking dan ekstraksi supaya menampilkan jumlah piksel yang valid dan jumlah piksel yang diekstrak.
    * Menambahkan visualisasi progress bar ke fungsi `ekstrak_tumpukan_fitur()`.
    * Memuat proses transformasi dan segmentasi ke dalam fungsi di modul `transformasi.py`.
* **Perbaikan Bug**:
    * Memodfikasi fungsi `clip_raster()` supaya nilai piksel 0 tidak hilang.

### Versi 1.4.4 - 30 Oktober 2025
* **Fitur Baru**:
    * Memodifikasi fungsi `ambil_file()` supaya menampilkan daftar file yang relevan.
    * Menambahkan fungsi `tumpuk_fitur()` untuk menumpuk semua fitur berdasarkan list.
    * Menambahkan `model_random_forest_0.joblib` sebagai model klasifikasi padi dan gulma.
    * Menambahkan `segmentasi_gulma.py` untuk menjalankan klasifikasi pad dan gulma.
* **Perbaikan Bug**:
    * Mengganti nilai nodata menjadi NaN dari sebelumnya -9999 untuk menghindari galat.
    
### Versi 1.4.3 - 22 Oktober 2025
* **Fitur Baru**:
    * Menjadikan struktur proyek lebih fleksibel berdasarkan input pengguna.
    * Memuat bagian untuk menampilkan histogram ke dalam fungsi `tampilkan_histogram()`.
    * Menambahkan bagian untuk menampilkan hasil clipping.
* **Perbaikan Bug**:
    * Menghilangkan bounding box hitam di sekitar hasil clipping.
    * Memperbaiki bug lonjakan nilai 0 pada histogram akibat nilai nodata yang dihitung pada saat transformasi.

### Versi 1.4.2 - 21 Oktober 2025
* **Fitur Baru**:
    * Memuat bagian untuk meminta folder dan file ke dalam fungsi `ambil_file()`.
    * Menambahkan NDREI sebagai acuan thresholding untuk memisahkan antara tanaman dengan gulma.
* **Perbaikan Bug**:
    * Memperbaiki bug program terus berjalan meskipun folder atau file tidak valid. 
 
### Versi 1.4.1 - 13 Oktober 2025
* **Fitur Baru**:
    * Menambahkan fitur ekstraksi nilai piksel berdasarkan verteks poligon.
    * Memberikan fitur ekstraksi kemampuan untuk mengekstrak semua band dalam folder.
    * Menyimpan hasil ekstraksi dalam sebuah file `.csv`
    * Menampilkan progress bar untuk mengetahui kemajuan proses ekstraksi.
* **Perbaikan Bug**:
    * Mengubah lokasi folder hasil masking dan transformasi untuk memudahkan ekstraksi.
    * Memperbaiki masalah file yang overwrite.
    * Memperbaiki masalah NoData yang diekstrak ke `.csv`
    * Memperbaiki urutan alfabetis kolom ekstraksi menjadi sesuai kebutuhan.
    * Memperbaiki format data citra yang tidak konsisten.
    
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
