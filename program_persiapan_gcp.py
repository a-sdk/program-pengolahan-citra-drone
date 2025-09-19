
import pandas as pd

# Menentukan file csv
target_file = r"C:\Users\acer_\Documents\rumah.csv"
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
hapus_kolom = ['Notes', 'DMS', 'UTM', 'MGRS', 'CRS', 'CRS Code', 'Address', 'Date Record', 'Photo1', 'Photo2', 'Photo3']
# Menghapus kolom yang tidak perlu
df_hasil = df_urut.drop(columns=hapus_kolom)
print("Menampilkan pratinjau hasil proses...")
print(f"\n{df_hasil}")
# Menyimpan hasil ke csv
print("\nMenyimpan file...")
df_hasil.to_csv('rumah2.csv', index=False)
print("File Berhasil Disimpan")

