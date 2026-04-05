import os

def konversi_model(model_path, hasil, mode=None):
    from tf.keras.models import load_model

    model = load_model(model_path)
    nf = os.path.splitext(os.path.basename(model_path))[0]
    if mode == 'p':
        print("Menyimpan arsitektur dan bobot terpisah...")
        # simpan arsitektur
        with open(f"{hasil}/{nf}.json", "w") as f:
            f.write(model.to_json())

        # simpan bobot
        model.save_weights(f"{hasil}/{nf}.weights.h5")
        print("selesai")
    else:
        print("Menyimpan arsitektur dan bobot...")
        model.save(f"{hasil}/{nf}")



if __name__ == "__main__":
    model_path = "core/models/model_deteksi_penyakit_v1.keras"
    job = r"C:\mYdata\SKRRP\Belajar\Pengolahan_Citra_Multispektral\program_pengolahan_citra\core\models\model_deteksi_gulma.joblib"
    hasil = r"C:\mYdata\SKRRP\Belajar\Pengolahan_Citra_Multispektral\program_pengolahan_citra\core\models\deteksi_penyakit\model_deteksi_gulma_v1.joblib"
    # konversi_model(model_path, hasil, mode=None)


