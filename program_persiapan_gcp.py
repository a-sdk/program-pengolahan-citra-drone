
import pandas as pd
import numpy as np
# Menentukan file csv
target_file = r"C:\Users\acer_\Documents\tomo.csv"
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
# fill_values = {'Elevation(MSL)': 71.6}
# df_hasil.fillna(value=fill_values, inplace=True)
print("Menampilkan pratinjau hasil proses...")
print(f"\n{df_hasil}")
# Menyimpan hasil ke csv
print("\nMenyimpan file...")
df_hasil.to_csv('tomo2.csv', index=False)
print("File Berhasil Disimpan")

