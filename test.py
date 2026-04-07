def hitung(a, b):
    plus = [a, b, a + b]
    minus = [b, b, a - b]
    return [plus, minus]

tambah, kurang = hitung(7, 3)
print(tambah, kurang)