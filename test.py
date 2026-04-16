import numpy as np

data = [1, 1, 1, 2, 2, 3, 3, 3, 4, 4, 4, 2, 1]

counts = {k: v for k, v in zip(*np.unique(data, return_counts=True))}
labels = ["Healthy", "Low", "Mild", "Severe"]
# Menghitung persentase
persen = {k: round((counts.get(i+1, 0) / len(data)) * 100, 2) for i, k in enumerate(labels)}
# Mencetak hasil
print(f"Total piksel pada citra: {len(data)}")
for i, label in enumerate(labels, 1):
    print(f"Persentase tanaman {label}: {persen[label]}%")