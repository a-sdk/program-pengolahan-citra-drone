'''
Modul untuk ekstraksi fitur citra.
'''

# Libraries
import numpy as np
import pandas as pd
import rasterio as rio
from rasterio.windows import from_bounds
from rasterio.features import geometry_mask
from rasterstats import zonal_stats
import geopandas as gpd
import os
import glob
import gc
from mahotas.polygon import fill_polygon
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)

# Fungsi untuk membuat polygon sebagai grid titik (mmuhaemin)
def render(poly):
    """
    Membuat grid titik dari poligon berdasarkan koordinat piksel.
    Mengembalikan daftar semua koordinat piksel (row, col) di dalam poligon.
    """
    xs, ys = zip(*poly)
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    newPoly = [(int(x - minx), int(y - miny)) for (x, y) in poly]
    grid = np.zeros((maxx - minx + 1, maxy - miny + 1), dtype=np.int8)
    fill_polygon(newPoly, grid)
    return [(x + minx, y + miny) for (x, y) in zip(*np.nonzero(grid))]

# Fungsi untuk mengekstrak koordinat verteks dari satu file multipoligon (nurrohman)
def ekstrak_koordinat_vertek(shp_path, output_folder):
    """
    Mengekstrak koordinat vertek dari setiap komponen multipoligon
    menjadi file .CSV terpisah

    Parameters:
        shp_path (str): Lokasi shapefile yang menjadi acuan.
        output_folder (str): Nama folder tempat file akan disimpan.

    Returns:
        None.
    """
   
    os.makedirs(output_folder, exist_ok=True)

    print(f"Membaca file: {shp_path}...")
    gdf = gpd.read_file(shp_path)
    gdf["no_urut"] = gdf.groupby("id").cumcount() + 1
    total_rows = len(gdf)
    
    print(f"Ditemukan {total_rows} komponen poligon.")

    for i, row in gdf.iterrows():
        geometry = row.geometry
        polygon_id = row["id"]
        komponen_id = row["no_urut"]
        polygon_index = i + 1
        # Cek tipe geometri dan ambil koordinatnya
        if geometry.geom_type == "Polygon":
            coords = list(geometry.exterior.coords)
        elif geometry.geom_type == "MultiPolygon":
            coords = list(geometry.geoms[0].exterior.coords)
        else:
            continue

        df = pd.DataFrame(coords, columns=["X", "Y"])
        df["id"] = polygon_id
        csv_filename = f"Poligon {polygon_id} Komponen {komponen_id}.csv"
        csv_filepath = os.path.join(output_folder, csv_filename)
        
        df.to_csv(csv_filepath, index=False)
        
        if polygon_index % 100 == 0:
            print(f"Telah memproses {polygon_index}/{total_rows} poligon...")

    print(f"Selesai! {total_rows} CSV telah disimpan di: {output_folder}")

# Fungsi untuk mengekstrak nilai piksel berdasarkan koordinat verteks
def ekstrak_piksel_dari_vertek(input_vertek, input_folder, output_folder, output_filename):
    """
    Mengekstrak seluruh nilai piksel dalam poligon berdasarkan koordinat verteks.

    Parameters:
        input_vertek (str): Lokasi file koordinat vertek.
        input_folder (str): Lokasi folder raster yang akan diekstrak.
        output_folder (str): Nama folder tempat file akan disimpan.
        output_filename (str): Nama file output, termasuk ekstensi.

    Returns:
        None.
    """
    file_ekstraksi = glob.glob(os.path.join(input_folder, "*tif"))  # Mengambil semua file .tif yang ingin diekstrak
    # Membaca file verteks
    df = pd.read_csv(input_vertek)
    df["no_urut"] = df.groupby("id").cumcount() + 1
    df["Nama"] = "Poligon " + df["id"].astype(str) + " Komponen " + df["no_urut"].astype(str)

    grup = df.groupby("id")
    hasil_gabungan_band = None 
    # Memproses setiap file dalam folder
    for file in file_ekstraksi:
        nama_band = os.path.splitext(os.path.basename(file))[0] 
        with rio.open(file) as src:
            band_data = src.read(1)
            transform = src.transform

        hasil_ekstraksi = []

        # Memproses setiap poligon berdasarkan ID
        for id_poligon, data in tqdm(grup, desc=f"Mengkestrak {nama_band}", unit=" poligon", total=len(grup)):
            xs, ys = data["X"].to_numpy(), data["Y"].to_numpy()
            # Konversi koordinat UTM ke baris dan kolom raster
            rows, cols = rio.transform.rowcol(transform, xs, ys)
            vertek = list(zip(rows, cols))
            # Menentukan semua piksel di dalam poligon
            x1, y1 = zip(*render(vertek))
            # Mengambil nilai piksel dan konversi ke koordinat spasial
            for (r, c) in zip(x1, y1):
                nilai_piksel = band_data[r, c]
                X, Y = rio.transform.xy(transform, r, c)
                # Lewati nilai piksel nodata
                if np.isnan(nilai_piksel):
                    continue 
                nama_titik = data["Nama"].iloc[0]
                hasil_ekstraksi.append({
                    "id": id_poligon,
                    "Nama": nama_titik,
                    "row": r,
                    "col": c,
                    "X": X,
                    "Y": Y,
                    nama_band: nilai_piksel
                })
            
            tqdm.write(f"Poligon {id_poligon} selesai ({len(x1)} piksel)")

        df_band = pd.DataFrame(hasil_ekstraksi)

        # Menggabungkan hasil ekstraksi 
        if hasil_gabungan_band is None:
            hasil_gabungan_band = df_band
        else: 
            hasil_gabungan_band = pd.merge(
                hasil_gabungan_band, 
                df_band,
                on=["id", "Nama", "row", "col", "X", "Y"],
                how="inner"
            )

    # Menyimpan hasil ekstraksi ke CSV
    os.makedirs(output_folder, exist_ok=True)
    hasil_proses = os.path.join(output_folder, output_filename)
    urutan_band = ["RED", "GREEN", "BLUE", "M_GREEN", "M_RED", "RED_EDGE", "NIR", "GNDVI", "NDREI", "NDVI", "SAVI"]
    kolom_awal = ["id", "Nama", "row", "col", "X", "Y"] # kolom_awal = ["id", "row", "col", "X", "Y"]
    kolom_akhir = kolom_awal + [b for b in urutan_band if b in hasil_gabungan_band.columns] 
    hasil_gabungan_band = hasil_gabungan_band[kolom_akhir]
    hasil_gabungan_band.to_csv(hasil_proses, index=False)
    print(f"Ekstraksi selesai...")
    print(f"Total piksel yang diekstrak: {hasil_gabungan_band.shape[0]} piksel")
    print(rf"File {output_filename} berhasil disimpan di {output_folder}")

# Fungsi untuk mengekstrak nilai piksel dari folder kumpulan koordinat verteks
def ekstrak_piksel_setiap_koordinat(folder_vertek, folder_raster, output_folder):
    """
    Looping untuk ekstrak piksel dari banyak file CSV koordinat vertek.

    Parameters:
        folder_vertek (str): Lokasi folder koordinat vertek.
        folder_raster (str): Lokasi folder raster yang akan diekstrak.
        output_folder (str): Nama folder tempat file akan disimpan.

    Returns:
        None.
    """
    # Mencari semua file .csv di folder input
    daftar_csv = glob.glob(os.path.join(folder_vertek, "*.csv"))
    
    print(f"Ditemukan {len(daftar_csv)} file CSV untuk diproses.")
    
    for path_csv in daftar_csv:
        nama_file_asli = os.path.basename(path_csv)
        nama_output = f"Hasil_Ekstraksi_{nama_file_asli}"
        
        print(f"\n--- Memproses file: {nama_file_asli} ---")
        
        try:
            ekstrak_piksel_dari_vertek(
                input_vertek=path_csv,
                input_folder=folder_raster,
                output_folder=output_folder,
                output_filename=nama_output
            )
        except Exception as e:
            print(f"Gagal memproses {nama_file_asli}: {e}")
            continue
    
    all_files = glob.glob(os.path.join(output_folder, "*.csv"))
    df_total = pd.concat((pd.read_csv(f) for f in all_files), ignore_index=True)
    df_total.to_csv(os.path.join(output_folder, "Gabungan_Hasil_Ekstraksi.csv"), index=False)

# Fungsi untuk mengekstrak nilai piksel dari tumpukan fitur
def ekstrak_tumpukan_fitur(shp_path, input_folder, output_folder, output_filename):
    """
    Mengekstrak seluruh nilai piksel dalam poligon dari tumpukan fitur.

    Parameters:
        shp_path (str): Lokasi shapefile yang menjadi acuan.
        input_folder (str): Lokasi file tumpukan fitur.
        output_folder (str): Nama folder tempat file akan disimpan.
        output_filename (str): Nama file output, termasuk ekstensi.

    Returns:
        None.
    """
    X_data = []

    gdf = gpd.read_file(shp_path)
    gdf["no_urut"] = gdf.groupby("id").cumcount() + 1
    gdf["Nama"] = "Poligon " + gdf["id"].astype(str) + " Komponen " + gdf["no_urut"].astype(str)

    with rio.open(input_folder) as src:
        nodata_val = src.nodata if src.nodata is not None else np.nan
        
        for index, row in tqdm(gdf.iterrows(), desc="Mengekstrak piksel", total=len(gdf)):
            geom = row.geometry
            id_poligon = row["id"]
            nama_titik = row["Nama"]

            # 1. Hitung window (bounding box) dari poligon
            left, bottom, right, top = geom.bounds
            window = from_bounds(left, bottom, right, top, src.transform)
            
            # Bulatkan window agar sesuai dengan grid pixel
            window = window.round_offsets().round_lengths()
            
            # 2. Baca data HANYA di area window tersebut (Hemat RAM!)
            # Out_image shape: (bands, window_height, window_width)
            out_image = src.read(window=window).astype("float32")
            window_transform = src.window_transform(window)

            # Membuat mask poligon dalam window
            mask_poligon = geometry_mask([geom], 
                                         out_shape=(out_image.shape[1], out_image.shape[2]), 
                                         transform=window_transform, 
                                         invert=True)

            # Mengmbil indeks piksel yang berada di dalam poligon
            rows, cols = np.where(mask_poligon)
            
            if len(rows) == 0:
                continue

            # Mendapatkan nilai piksel untuk semua band sekaligus
            nilai_bands = out_image[:, rows, cols] # Shape: (jumlah_band, jumlah_piksel)

            # Mendapatkan koordinat X dan Y spasial
            xs, ys = rio.transform.xy(window_transform, rows, cols)

            # Menyusun data secara horizontal
            # Koordinat + Nilai Band
            data_piksel = np.vstack([np.array(xs), np.array(ys), nilai_bands]).T
            
            # Tambahkan kolom ID dan Nama
            id_col = np.full((data_piksel.shape[0], 1), id_poligon, dtype=object)
            nama_col = np.full((data_piksel.shape[0], 1), nama_titik, dtype=object)
            
            fitur_lengkap = np.hstack([id_col, nama_col, data_piksel])
            X_data.append(fitur_lengkap)

    # Menggabungkan semua data jika ada
    if X_data:
        X = np.vstack(X_data)
        nama_kolom = ["id", "Nama", "X", "Y", "RED", "GREEN", "BLUE", "M_GREEN", 
                      "M_RED", "RED_EDGE", "NIR", "GNDVI", "NDREI", "NDVI", "SAVI"]
        
        df = pd.DataFrame(X, columns=nama_kolom)
        # Hapus baris yang mengandung nodata (opsional)
        df = df.dropna(subset=["RED"]) 
        
        os.makedirs(output_folder, exist_ok=True)
        df.to_csv(os.path.join(output_folder, output_filename), index=False)
        print(f"Ekstraksi selesai. Total: {len(df)} piksel.")
    else:
        print("Tidak ada piksel yang diekstrak.")

# Fungsi untuk mengekstrak tumpukan fitur (band) dengan lebih sedikit RAM
def ekstrak_tumpukan_fitur_optimized(shp_path, input_folder, output_folder, output_filename):
    """
    Mengekstrak seluruh nilai piksel dalam poligon dari tumpukan fitur.

    Parameters:
        shp_path (str): Lokasi shapefile yang menjadi acuan.
        input_folder (str): Lokasi file tumpukan fitur.
        output_folder (str): Nama folder tempat file akan disimpan.
        output_filename (str): Nama file output, termasuk ekstensi.

    Returns:
        None.
    """

    output_path = os.path.join(output_folder, output_filename)
    os.makedirs(output_folder, exist_ok=True)

    gdf = gpd.read_file(shp_path)
    gdf["no_urut"] = gdf.groupby("id").cumcount() + 1
    gdf["Nama"] = "Poligon " + gdf["id"].astype(str) + " Komponen " + gdf["no_urut"].astype(str)

    nama_kolom = ["id", "Nama", "X", "Y", "RED", "GREEN", "BLUE", "M_GREEN", 
                  "M_RED", "RED_EDGE", "NIR", "GNDVI", "NDREI", "NDVI", "SAVI"]
    total_jml_piksel = 0
    with rio.open(input_folder) as src:
        # Menulis header CSV sekali
        pd.DataFrame(columns=nama_kolom).to_csv(output_path, index=False)
        
        for index, row in tqdm(gdf.iterrows(), desc="Mengekstrak piksel", total=len(gdf)):
            geom = row.geometry

            # Windowed Reading (Hanya bagian kecil citra)
            left, bottom, right, top = geom.bounds
            window = from_bounds(left, bottom, right, top, src.transform).round_offsets().round_lengths()
            
            # Cek jika window valid (menghindari poligon di luar jangkauan citra)
            if window.width < 1 or window.height < 1: continue

            out_image = src.read(window=window).astype("float32")
            window_transform = src.window_transform(window)

            # Membuat mask poligon dalam window
            mask_poligon = geometry_mask([geom], 
                                         out_shape=(out_image.shape[1], out_image.shape[2]), 
                                         transform=window_transform, 
                                         invert=True)

            rows, cols = np.where(mask_poligon)


            # Mengekstrak nilai piksel
            nilai_bands = out_image[:, rows, cols]
            mask_valid_piksel = (nilai_bands[6] != src.nodata) & (~np.isnan(nilai_bands[6]))
            nilai_bands = nilai_bands[:, mask_valid_piksel]
            rows_valid = rows[mask_valid_piksel]
            cols_valid = cols[mask_valid_piksel]
            if len(rows_valid) == 0: continue
            jml_piksel_poligon = len(rows_valid)
            total_jml_piksel += jml_piksel_poligon
            xs, ys = rio.transform.xy(window_transform, rows_valid, cols_valid)
            # Menyusun data poligon
            data_piksel = np.vstack([np.array(xs), np.array(ys), nilai_bands]).T
            id_col = np.full((data_piksel.shape[0], 1), row["id"], dtype=object)
            nama_col = np.full((data_piksel.shape[0], 1), row["Nama"], dtype=object)
            
            df_temp = pd.DataFrame(np.hstack([id_col, nama_col, data_piksel]), columns=nama_kolom)
            
            # Langsung tulis ke CSV, lalu hapus dari RAM
            df_temp.to_csv(output_path, mode='a', header=False, index=False)
            
            del df_temp # Paksa hapus dari memori setiap iterasi
            gc.collect()

    print(f"Ekstraksi selesai. Total: {total_jml_piksel} piksel.")
    print(f"Selesai! Data disimpan secara bertahap di: {output_path}")

class Extractor:
    """
    Kelas untuk ekstrak rerata piksel citra.
    """
    def __init__(self):
        self.status = "Idle"
        self.last_result = None

    def run(self, shp_path, input_folder, output_folder):
        self.status = "Processing"
        logger.info("Memulai proses ekstraksi...") 
        try:
            self.last_result = self.ekstrak_rerata_piksel(shp_path, input_folder, output_folder) 
            self.status = "Done"
            return self.last_result
        except Exception as e:
            self.status = "Error"
            logger.error(f"ERROR {type(e).__name__}: {e}", exc_info=True)
            return None
        
    # Fungsi untuk mengekstrak rata-rata nilai piksel dalam sub poligon
    def ekstrak_rerata_piksel(self, shp_path, input_folder, output_folder, output_filename="hasil_ekstrak.csv"):
        """
        Mengekstrak rata-rata piksel dalam poligon dari tumpukan fitur.

        Parameters:
            shp_path (str): Lokasi shapefile yang menjadi acuan.
            input_folder (str): Lokasi file tumpukan fitur.
            output_folder (str): Nama folder tempat file akan disimpan.
            output_filename (str): Nama file output, termasuk ekstensi.

        Returns:
            str: Output path.
        """

        gdf = gpd.read_file(shp_path)

        # Menyiapkan kolom identitas
        # gdf["no_urut"] = gdf.groupby("id").cumcount() + 1
        gdf["Nama"] = "Poligon " + gdf["id"].astype(str) + " Komponen " + gdf["no_urut"].astype(str)
        
        # Mengambil koordinat X dan Y dari centroid poligon
        gdf["X"] = gdf.geometry.centroid.x
        gdf["Y"] = gdf.geometry.centroid.y

        # Menyiapkan DataFrame hasil dengan kolom koordinat awal
        hasil_ekstraksi = gdf[["id", "no_urut", "Nama", "X", "Y"]].copy()
        
        with rio.open(input_folder) as info:
            count = info.count
        
        if count > 7:
            nama_bands = [
                "RED", "GREEN", "BLUE", "M_GREEN", "M_RED", 
                "RED_EDGE", "NIR", "GNDVI", "NDREI", "NDVI", "SAVI"
            ]
        else:
            nama_bands = [
                "RED", "GREEN", "BLUE", "M_GREEN", "M_RED", 
                "RED_EDGE", "NIR"
            ]

        nf = os.path.splitext(os.path.basename(input_folder))[0]
        print(f"\nMemuat hasil masking: {nf}")
        with rio.open(input_folder) as src:
            for i, nama_band in tqdm(enumerate(nama_bands), desc="Mengekstrak rerata piksel", unit=" band", total=len(nama_bands)):
                band_data = src.read(i + 1)
                
                stats = zonal_stats(
                    vectors=gdf, 
                    raster=band_data, 
                    affine=src.transform, 
                    stats=["mean"], 
                    nodata=src.nodata,
                    all_touched=True # Mengambil semua piksel yang bersentuhan
                )
                
                mean_values = [s.get("mean", src.nodata) for s in stats]
                hasil_ekstraksi[nama_band] = mean_values

        # Cek baris yang mengandung NaN sebelum dihapus
        df_lengkap = pd.DataFrame(hasil_ekstraksi)
        nan_rows = df_lengkap[df_lengkap.isna().any(axis=1)]
        
        if not nan_rows.empty:
            print(f"\nPERHATIAN: Ditemukan {len(nan_rows)} poligon dengan nilai piksel tidak valid (NaN).")
            print(f"Poligon yang bermasalah: {nan_rows['Nama'].tolist()}")
        # ------------------------
        # Pembersihan dan pengurutan data
        print(f"Membersihkan hasil ekstraksi...")
        df = pd.DataFrame(hasil_ekstraksi).dropna()
        df_urut = df.sort_values(by=["id", "no_urut"], ascending=True)
        df_urut = df_urut.drop(columns=["id"])
        df_urut.rename(columns={"no_urut": "id"}, inplace=True)
        
        # Simpan file
        os.makedirs(output_folder, exist_ok=True)
        output_path = os.path.join(output_folder, output_filename)
        df_urut.to_csv(output_path, index=False)
        
        print(f"Ekstraksi selesai...")
        print(f"Total baris yang diekstrak: {df_urut.shape[0]}")
        print(rf"File {output_filename} berhasil disimpan di {output_folder}")    
        return output_path          
