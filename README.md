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

Pastikan Anda telah mengunduh aplikasi (.exe) dan folder internalnya yang dimuat dalam zip.

### Instalasi

Ekstrak zip tersebut di folder lokal Anda.

Jalankan aplikasi (.exe) dan tunggu hingga muncul tampilan.


## Struktur Proyek

```text
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
