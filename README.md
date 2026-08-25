# Program Pengolahan Citra Drone Multispektral

## Deskripsi Proyek

Proyek ini adalah program untuk mengolah citra udara dari drone sehingga menghasilkan peta sebaran.

## Fitur Utama

1. Memuat citra raster GeoTiff.
2. Memuat vektor seperti shapefile dan geopackage.
3. Membuat dan menggambar poligon.
4. Memproses raster GeoTiff menggunakan model machine learning.
5. Menampilkan peta sebaran hasil prediksi model machine learning.
6. Memberikan informasi sebaran dan rekomendasi tindakan.


## Panduan Instalasi 

Ikuti langkah-langkah berikut untuk menjalankan proyek di komputer lokal Anda.

### Persyaratan

Pastikan Anda telah mengunduh file zip yang memuat aplikasi (.exe) dan folder internalnya.

### Instalasi

Ekstrak zip tersebut di folder lokal Anda.

Jalankan aplikasi (.exe) dan tunggu hingga muncul tampilan.

## Panduan Penggunaan
### Tampilan Awal Aplikasi
Setelah aplikasi berhasil dibuka, tampilan awal yang muncul seperti berikut. Terdapat menu, toolbar, dan panel kosong.
<img width="1922" height="1042" alt="Image" src="https://github.com/user-attachments/assets/233ff5e9-5586-44cd-8662-7f3fa0b24c87" />
### Add Raster
Tekan tombol `Add Raster` pada toolbar untuk menambahkan file GeoTIFF ke aplikasi, file tersebut akan dimuat dan ditampilkan pada aplikasi.

<img width="234" height="110" alt="Image" src="https://github.com/user-attachments/assets/3237feb2-811b-4bea-bf7f-a902fd77c9b4" />
<img width="1921" height="1042" alt="Image" src="https://github.com/user-attachments/assets/522245fd-bd20-4860-bbe6-932ea72bf08a" />
<img width="1920" height="1040" alt="Image" src="https://github.com/user-attachments/assets/52551814-e48a-41f9-b4b2-16697199b873" />
### Add Vector
Tekan tombol `Add Vector` pada toolbar untuk menambahkan file vektor seperi shapefile (.shp) atau geopackage (.gpkg), kemudian file akan dimuat dan ditampilkan pada aplikasi. 
<img width="1921" height="1042" alt="Image" src="https://github.com/user-attachments/assets/b786284a-4113-4f7f-885b-dd6a3b699b20" />
### Create New Shapefile
Jika ingin membuat atau menggambar shapefile, tekan tombol `Create New Shapefile` pada toolbar. Selanjutnya, dialog pembuatan shapefile akan muncul dan dapat disesuaikan dengan kebutuhan. 
<img width="309" height="116" alt="Image" src="https://github.com/user-attachments/assets/60ba37f7-af65-40de-99bf-4d393dcbd139" />
<img width="309" height="184" alt="Image" src="https://github.com/user-attachments/assets/81b83d95-9d2a-4f76-bd6b-a29f3824422c" />
Mode gambar ditandai dengan munculnya instruksi di kanan bawah aplikasi dan kursor berubah menjadi `+`
<img width="591" height="68" alt="Image" src="https://github.com/user-attachments/assets/4852e717-7ab6-4b67-83f2-11f70d18b3be" />
### Pan/Zoom
Tombol `Pan`, `Zoom In/Out`, juga `Fit to View` dapat digunakan untuk menyesuaikan tampilan yang muncul di aplikasi sesuai dengan yang diperlukan. 
<img width="281" height="161" alt="Image" src="https://github.com/user-attachments/assets/517417ad-141e-473d-98f1-ddb283e28cbf" />
### Prediksi Model
Menu prediksi model machine learning dapat diakses pada toolbar yang terdiri dari tiga menu utama yakni prediksi nutrisi, air tersedia, dan penyakit tanaman. Menu akan memunculkan dialog yang memerlukan file GeoTiff, shapefile, dan direktori (folder) untuk menyimpan hasil prediksinya.
<img width="310" height="103" alt="Image" src="https://github.com/user-attachments/assets/a604fe7d-02aa-4f7b-b0be-28cd1185b017" />
<img width="469" height="241" alt="Image" src="https://github.com/user-attachments/assets/97e21cc6-d0bc-409f-87cf-e8668ebe30d7" />
Setiap menu prediksi menjalankan serangkaian proses yang ditunjukkan oleh pop-up seperti berikut hingga prosesnya selesai. 
<img width="673" height="384" alt="Image" src="https://github.com/user-attachments/assets/260990a3-5860-4077-a2c4-0474ae0e288e" />
<img width="195" height="153" alt="Image" src="https://github.com/user-attachments/assets/8f4e2926-7bac-4eed-9d23-e6adedf84f4e" />
Hasilnya kemudian ditampilkan dalam kode warna tertentu, informasi warna yang tampil juga dapat dilihat pada legenda. Sebagai contoh, berikut hasil prediksi ketersediaan air.
<img width="1921" height="1041" alt="Image" src="https://github.com/user-attachments/assets/06602a48-ac6f-406a-b5e7-a6c2a90abd53" />
Hasil prediksi kecukupan nutrisi meliputi nitrogen, phospor, dan kalium.
<img width="1921" height="1042" alt="Image" src="https://github.com/user-attachments/assets/b0657503-a927-4b3f-b7ed-78b2ffe6146e" />
Hasil prediksi serangan penyakit tanaman yang umum menyerang seperti blas, bercak daun, dan hawar daun.
<img width="1922" height="1040" alt="Image" src="https://github.com/user-attachments/assets/63b0aced-e53c-4396-abb0-b6cc05a241fb" />

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
