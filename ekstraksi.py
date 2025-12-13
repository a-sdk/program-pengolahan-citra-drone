'''
Modul untuk mask dan ekstraksi fitur citra.
'''

# Libraries
import numpy as np
import pandas as pd
import rasterio as rio
from rasterio.mask import mask
from rasterstats import zonal_stats
import geopandas as gpd
import os
import glob
from mahotas.polygon import fill_polygon
from tqdm import tqdm

# Fungsi untuk memotong citra bedasarkan shapefile poligon
def clip_raster(input_folder, shp_layer, output_folder, output_filename, nilai_nodata=np.nan):
    """
    Memotong citra sesuai dengan shaepfile poligon yang dibuat.

    Args:
        input_folder (str): Lokasi file raster yang akan dipotong.
        shp_layer (str): Lokasi shapefile yang menjadi acuan.
        output_folder (str): Nama folder tempat hasil klip disimpan.
        output_filename (str): Nama file output, termasuk ekstensi
        
    Returns:
        str: Output path.
    """
    konversi_path = f"{output_folder}/raster_float32.tif"
    # Tentukan lokasi hasil clip
    output_path = os.path.join(output_folder, output_filename)
    # Pastikan folder output ada, jika tidak, buat folder baru
    os.makedirs(output_folder, exist_ok=True)
    # Baca Shapefile Menggunakan GeoPandas
    print("Memuat shapefile...")
    print("Mengkonversi citra...")
    mask_gdf = gpd.read_file(shp_layer)
    with rio.open(input_folder) as src:
        data = src.read()
        profile = src.profile
    profile.update(
        dtype="float32",
        BIGTIFF="YES",
        nodata=nilai_nodata
        )
    # Mengkonversi ke format float32
    with rio.open(konversi_path, "w", **profile) as dest:
        dest.write(data.astype("float32"))

    # Membuka raster float32
    with rio.open(konversi_path) as src_32:
        geometries = mask_gdf.geometry
        profile32 = src_32.profile
        # Melakukan masking
        print("Memotong raster berdasarkan shapefile...")
        out_image, out_transform = mask(
            src_32,
            geometries, 
            crop=True,
            filled=True
            )
    # Perbarui metadata dengan informasi dari hasil clip
    profile32.update(
        dtype="float32",
        height=out_image.shape[1],
        width=out_image.shape[2],
        count=out_image.shape[0],
        transform=out_transform,
        BIGTIFF="YES",
        nodata=nilai_nodata,
        driver="GTiff"
    )
    print("Menyimpan hasil clipping...")
    with rio.open(output_path, "w", **profile32) as dest:
        dest.write(out_image)
    print(f"File {output_filename} berhasil disimpan di {output_folder}")
    os.remove(konversi_path)
    return output_path

# Fungsi memotong citra dengan penghematan memori 
def clip_raster_optimized(input_folder, shp_layer, output_folder, output_filename, nilai_nodata=np.nan):
    """
    Memotong citra sesuai dengan shaepfile poligon yang dibuat, 
    menggunakan pemrosesan berblok untuk menghemat RAM saat konversi uint16 -> float32.

    Args:
        input_folder (str): Lokasi file raster yang akan dipotong.
        shp_layer (str): Lokasi shapefile yang menjadi acuan.
        output_folder (str): Nama folder tempat hasil klip disimpan.
        output_filename (str): Nama file output, termasuk ekstensi
        
    Returns:
        str: Output path.
    """
    konversi_path = f"{output_folder}/raster_float32.tif"
    output_path = os.path.join(output_folder, output_filename)
    os.makedirs(output_folder, exist_ok=True)

    print("Memuat shapefile...")
    mask_gdf = gpd.read_file(shp_layer)

    print("Mengkonversi citra...")
    with rio.open(input_folder) as src:
        profile = src.profile
        profile.update(
            dtype="float32",
            BIGTIFF="YES",
            nodata=nilai_nodata,
            tiled=True,
            blockxsize=256, 
            blockysize=256
        )
        old_nodata = src.nodata

        with rio.open(konversi_path, "w", **profile) as dest:
            for ji, window in src.block_windows():
                block = src.read(window=window, out_dtype=np.uint16)
                
                block_f32 = block.astype(np.float32)
                if old_nodata is not None:
                    block_f32[block_f32 == old_nodata] = np.nan
            
                dest.write(block_f32, window=window)

    with rio.open(konversi_path) as src_32:
        geometries = mask_gdf.geometry
        profile32 = src_32.profile
        
        print("Memotong raster berdasarkan shapefile...")
        out_image, out_transform = mask(
            src_32,
            geometries, 
            crop=True,
            filled=True,
            nodata=nilai_nodata 
        )
        

    profile32.update(
        dtype="float32",
        height=out_image.shape[1],
        width=out_image.shape[2],
        count=out_image.shape[0],
        transform=out_transform,
        BIGTIFF="YES",
        nodata=nilai_nodata,
        driver="GTiff"
    )
    
    print("Menyimpan hasil clipping...")
    with rio.open(output_path, "w", **profile32) as dest:
        dest.write(out_image)

    print(f"File {output_filename} berhasil disimpan di {output_folder}")
    os.remove(konversi_path)
    
    return output_path

# Fungsi untuk melakukan masking pada setiap band terpisah
def mask_band_terpisah(input_folder, mask_path, output_folder, logika=lambda x: x==1, nilai_nodata=np.nan):
    """
    Menerapkan masking pada band berdasarkan mask boolean.
    
    Args:
        input_folder (str): Lokasi folder raster yang akan di-mask.
        mask_path (str): Lokasi file mask.
        output_folder (str): Nama folder tempat hasil mask disimpan.
        logika (function): Fungsi lambda sebagai acuan mask.
        nilai_nodata (float): Nilai nodata raster.
    
    Returns:
        None.
    """
    print("\nMemuat mask...")
    with rio.open(mask_path) as src_mask:
        mask_data = src_mask.read(1)
    # Membuat boolean mask
    mask_valid = logika(mask_data)
    # Mengecualikan nilai nodata
    mask_valid[np.isnan(mask_data)] = False
    print(f"Mask boolean berhasil dibuat. Total piksel valid: {np.sum(mask_valid)}")
    # Menerapkan mask pada semua file dalam input folder
    lst_file = glob.glob(os.path.join(input_folder, "*.tif"))
    if not lst_file:
        print(f"Tidak ada file .tif di {input_folder}")
    os.makedirs(output_folder, exist_ok=True)
    print(f"Menerapkan mask ke {len(lst_file)} band")
    for file in lst_file:
        nf = os.path.basename(file)
        output_path = os.path.join(output_folder, nf)
        with rio.open(file) as src:
            data = src.read(1)
            profile = src.profile
        data[~mask_valid] = nilai_nodata
        profile.update(
            dtype="float32",
            nodata=nilai_nodata
        )
        print("Menyimpan hasil masking...")
        with rio.open(output_path, "w", **profile) as dest:
            dest.write(data, indexes=1)
        print(f"File {nf} berhasil disimpan di {output_folder}")

# Fungsi untuk melakukan masking pada tumpukan band
def mask_tumpukan_band(input_folder, mask_path, output_folder, logika=lambda x: x==1, nilai_nodata=np.nan):
    """
    Menerapkan masking pada tumpukan band berdasarkan mask boolean.
    
    Args:
        input_folder (str): Lokasi folder tumpukan band yang akan di-mask.
        mask_path (str): Lokasi file mask.
        output_folder (str): Nama folder tempat hasil mask disimpan.
        logika (function): Fungsi lambda sebagai acuan mask.
        nilai_nodata (float): Nilai nodata raster.
    
    Returns:
        None.
    """
    print("\nMemuat mask...")
    with rio.open(mask_path) as src_mask:
            mask_data = src_mask.read(1)
    # Membuat boolean mask
    mask_valid = logika(mask_data)
    # Mengecualikan nilai nodata
    mask_valid[np.isnan(mask_data)] = False           
    print(f"Mask boolean berhasil dibuat. Total piksel valid: {np.sum(mask_valid)}")
    print(f"Membuka tumpukan band...")
    nf = os.path.splitext(os.path.basename(input_folder))[0]
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, f"{nf}_masked.tif")
    with rio.open(input_folder) as src_data:
        # Membaca band sekaligus
        data_stack = src_data.read()
        profile = src_data.profile
        print("Menerapkan mask ke semua band...")
        data_stack[:, ~mask_valid] = nilai_nodata
        
        # Perbarui profile untuk file output agar konsisten
        profile.update(
            dtye="float32",
            count=data_stack.shape[0], 
            nodata=nilai_nodata
        )
        print("Menyimpan hasil masking...")
        with rio.open(output_path, "w", **profile) as dest:
            dest.write(data_stack)
    print(f"File {nf}_masked.tif berhasil disimpan di {output_folder}")

# Fungsi untuk membuat polygon sebagai grid titik
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

# Fungsi untuk mengekstrak nilai piksel berdasarkan koordinat verteks
def ekstrak_piksel_dari_vertek(input_vertek, input_folder, output_folder, output_filename):
    """
    Mengekstrak seluruh nilai piksel dalam poligon berdasarkan koordinat verteks.

    Args:
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
        for id_poligon, data in tqdm(grup, desc=f"\nMengkestrak {nama_band}", unit=" poligon", total=len(grup)):
            # nama_poli = data["NAME"].iloc[0]
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

                hasil_ekstraksi.append({
                    "id": id_poligon,
                    # "NAME": nama_poli,
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
                on=["id", "row", "col", "X", "Y"],
                how="inner"
            )

    # Menyimpan hasil ekstraksi ke CSV
    os.makedirs(output_folder, exist_ok=True)
    hasil_ekstraksi = os.path.join(output_folder, output_filename)
    urutan_band = ["RED", "GREEN", "BLUE", "M_GREEN", "M_RED", "RED_EDGE", "NIR", "GNDVI", "NDREI", "NDVI", "SAVI"]
    kolow_awal = "id" # kolom_awal = ["id", "row", "col", "X", "Y"]
    kolom_akhir = kolow_awal + [b for b in urutan_band if b in hasil_gabungan_band.columns] 
    hasil_gabungan_band = hasil_gabungan_band[kolom_akhir]
    hasil_gabungan_band.to_csv(hasil_ekstraksi, index=False)
    print(f"Ekstraksi selesai...")
    print(f"Total piksel yang diekstrak: {hasil_gabungan_band.shape[0]} piksel")
    print(rf"File {output_filename} berhasil disimpan di {output_folder}")

# Fungsi untuk mengekstrak nilai piksel dari tumpukan fitur
def ekstrak_tumpukan_fitur(shp_layer, input_folder, output_folder, output_filename):
    """
    Mengekstrak seluruh nilai piksel dalam poligon dari tumpukan fitur.

    Args:
        shp_layer (str): Lokasi shapefile yang menjadi acuan.
        input_folder (str): Lokasi file tumpukan fitur.
        output_folder (str): Nama folder tempat file akan disimpan.
        output_filename (str): Nama file output, termasuk ekstensi.

    Returns:
        str: None.
    """
    file_ekstraksi = glob.glob(os.path.join(input_folder, "*tif"))  # Mengambil semua file .tif yang ingin diekstrak
    X_data = [] # Untuk menyimpan fitur

    gdf = gpd.read_file(shp_layer)

    for file in file_ekstraksi:
        with rio.open(file) as src:
            for index, row in tqdm(gdf.iterrows(), desc="\nMengekstrak piksel", unit=" poligon", total=len(gdf)):

                geometry = [row.geometry]
                id_poligon = row["id"]
                
                # Memotong tumpukan 11-band menggunakan poligon
                out_image, _ = mask(src, geometry, crop=True, nodata=np.nan)
                
                # Menentukan piksel yang valid
                valid_mask_2d = ~np.isnan(out_image[0])
                
                # Menyiapkan array kosong
                ekstrak_piksel = []
                for band_idx in range(src.count): 
                    band_data = out_image[band_idx]
                    piksel_valid = band_data[valid_mask_2d]
                    ekstrak_piksel.append(piksel_valid)

                # Transpose array
                fitur_piksel = np.array(ekstrak_piksel).T # (jumlah_piksel, 11)
                
                kolom_id = np.full(fitur_piksel.shape[0], id_poligon)
                fitur_lengkap = np.column_stack((kolom_id, fitur_piksel))
                X_data.append(fitur_lengkap)

        # Gabungkan semua data
        X = np.concatenate(X_data, axis=0) # (total_piksel, 11 fitur)

    nama_kolom = [
        "id",
        "RED",
        "GREEN",
        "BLUE",
        "M_GREEN",
        "M_RED",
        "RED_EDGE",
        "NIR",
        "GNDVI",
        "NDREI",
        "NDVI",
        "SAVI"
    ]
    df = pd.DataFrame(X, columns=nama_kolom)
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, output_filename)
    df.to_csv(output_path, index=False)
    print(f"Ekstraksi selesai...")
    print(f"Total piksel yang diekstrak: {X.shape[0]} piksel")
    print(rf"File {output_filename} berhasil disimpan di {output_folder}")

# Fungsi untuk mengekstrak rata-rata nilai piksel dalam sub poligon
def ekstrak_rerata_piksel_multipol(shp_layer, input_folder, output_folder, output_filename):
    """
    Mengekstrak rata-rata piksel dalam poligon dari tumpukan fitur.

    Args:
        shp_layer (str): Lokasi shapefile yang menjadi acuan.
        input_folder (str): Lokasi file tumpukan fitur.
        output_folder (str): Nama folder tempat file akan disimpan.
        output_filename (str): Nama file output, termasuk ekstensi.

    Returns:
        str: None.
    """
    file_ekstraksi = glob.glob(os.path.join(input_folder, "*tif"))
    gdf = gpd.read_file(shp_layer)
    hasil_ekstraksi = gdf[["id"]].copy()
    nama_bands = [
        "RED",
        "GREEN",
        "BLUE",
        "M_GREEN",
        "M_RED",
        "RED_EDGE",
        "NIR",
        "GNDVI",
        "NDREI",
        "NDVI",
        "SAVI"
    ]
    for file in file_ekstraksi:
        with rio.open(file) as src:
            # Iterasi melalui band, membaca satu per satu
            for i, nama_band in tqdm(enumerate(nama_bands), desc="\nMengekstrak piksel", unit=" band", total=len(nama_bands)):
                # Membaca data band
                band_data = src.read(i + 1)
                # Melakukan Zonal Stats untuk band tersebut
                stats = zonal_stats(
                    vectors=gdf, 
                    raster=band_data, 
                    affine=src.transform, 
                    stats=['mean'], 
                    nodata=src.nodata
                )
                
                # Mendapatkan nilai rata-rata
                mean_values = [s.get("mean", np.nan) for s in stats]
                
                # Menambahkan kolom ke DataFrame hasil
                hasil_ekstraksi[nama_band] = mean_values
            
    df = pd.DataFrame(hasil_ekstraksi).dropna()
    df_urut = df.sort_values(by="id", ascending=True)
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, output_filename)
    df_urut.to_csv(output_path, index=False)
    print(f"Ekstraksi selesai...")
    print(f"Total rata-rata piksel yang diekstrak: {df_urut.shape[0]} piksel")
    print(rf"File {output_filename} berhasil disimpan di {output_folder}")
