# Program Pengolahan Citra Drone Multispektral

## Deskripsi Proyek

Proyek ini adalah program untuk mengolah citra udara dari drone sehingga menghasilkan peta sebaran.

## Fitur Utama

1. Memuat citra raster GeoTiff dan gambar biasa (.png/.jpg/.jpeg).
2. Memuat vektor seperti shapefile dan geopackage.
3. Membuat dan menggambar poligon.
4. Memproses raster GeoTiff menggunakan model machine learning.
5. Menampilkan peta sebaran hasil prediksi model machine learning.
6. Memberikan informasi sebaran dan rekomendasi tindakan.


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
├── assets/
│   ├── defaults/
│       ├── config/
│       ├── models/
│       ├── scalers/
│       └── textures/
├── changelogs/
├── core/
├── gui/
└── ui/


---
