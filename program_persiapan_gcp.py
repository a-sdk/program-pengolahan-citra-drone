
import pandas as pd
# Mengatur opsi tampilan untuk menampilkan 10 angka desimal
pd.set_option('display.precision', 10)
# Menentukan file csv
target_file = r"C:\Users\acer_\Downloads\sukabumi_cikembar.csv"
# Membaca file csv
print("\nMemuat file...")
df = pd.read_csv(target_file)
print("Membaca isi file...")
print(f"\n{df}")
# Mengganti "ID" dengan "Label"
print("\nMemproses file...")
df.rename(columns={'ID':'Label'}, inplace=True)
# Mendapatkan list semua kolom
kolom = df.columns.tolist()
# Menukar urutan kolom kedua (Latitude) dengan kolom ketiga (Longitude)
kolom[1], kolom[2] = kolom[2], kolom[1]
# Memodifikasi urutan kolom dataframe
df_urut = df[kolom]
# Menentukan kolom yang tidak diperlukan (akan dihapus)
hapus_kolom = ['Notes', 'DMS', 'UTM', 'MGRS', 'CRS', 'CRS Code', 'Address', 'Date Record', 'GPS Accuracy(m)', 'Photo1', 'Photo2', 'Photo3']
# Menghapus kolom yang tidak perlu
df_hasil = df_urut.drop(columns=hapus_kolom)
perlu_koreksi = input("Apakah perlu koreksi koordinat? (y/n): ")
if perlu_koreksi == "y":
    # Meminta pengguna untuk memasukkan semua nilai Longitude dalam satu baris
    longitudes_input = input("Masukkan nilai Longitude baru, dipisahkan dengan koma: ")
    # Minta pengguna untuk memasukkan semua nilai Latitude dalam satu baris
    latitudes_input = input("Masukkan nilai Latitude baru, dipisahkan dengan koma: ")
    # Minta pengguna untuk memasukkan semua nilai Elevation(MSL) dalam satu baris
    elevations_input = input("Masukkan nilai Elevation(MSL) baru, dipisahkan dengan koma: ")
    # Pisahkan string input menjadi daftar string dan konversi ke float
    new_longitudes = [float(val.strip()) for val in longitudes_input.split(',')]
    new_latitudes = [float(val.strip()) for val in latitudes_input.split(',')]
    new_elevations = [float(val.strip()) for val in elevations_input.split(',')]
    # Perbarui DataFrame
    df_hasil['Longitude'] = new_longitudes
    df_hasil['Latitude'] = new_latitudes
    df_hasil['Elevation(MSL)'] = new_elevations

print("Menampilkan pratinjau hasil proses...")
print(f"\n{df_hasil}")
# Menyimpan hasil ke csv
print("\nMenyimpan file...")
df_hasil.to_csv('sukabumi_gcp.csv', index=False)
print("File Berhasil Disimpan")

