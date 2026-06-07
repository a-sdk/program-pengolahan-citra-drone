# Program Pengolahan Citra Drone Multispektral

## Deskripsi Proyek

Proyek ini adalah program untuk mengolah citra udara yang ditangkap oleh drone sehingga menghasilkan data dalam bentuk CSV.

## Fitur Utama

1. Memotong citra berdasarkan poligon.
2. Membuat multipoligon dari sebuah shapefile poligon.
3. Mengekstrak koordinat vertek dari multipoligon.
4. Menghitung indeks vegetasi seperti SAVI, NDVI, NDRE, dan lainnya.
5. Melakukan segmentasi untuk memisahkan tanaman dan yang bukan tanaman.
6. Melakukan masking untuk menghapus data raster yang bukan berupa tanaman.
7. Mengekstrak nilai piksel citra dan atribut lainnya ke dalam file CSV.
8. Memeriksa ukuran raster.
9. Mendeteksi penyakit tanaman padi berdasarkan rumpun dan petak.
10. Membuat peta sebaran penyakit tanaman pati berdasarkan rumpun dan petak.



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

App/
│
├── main.py
├── path_config.py
│
├── app/
├── core/
├── gui/
├── ui/
├── assets/
│
├── runtime/
│   ├── models/
│   ├── scalers/
│   ├── config/
│   ├── cache/
│   └── logs/
│
└── temp/


---
