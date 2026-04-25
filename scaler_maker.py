from sklearn.preprocessing import StandardScaler, PolynomialFeatures 
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import tensorflow as tf

import pandas as pd
import numpy as np
import joblib
def r_square_metric(y_true, y_pred):
    SS_res = tf.reduce_sum(tf.square(y_true - y_pred))
    SS_tot = tf.reduce_sum(tf.square(y_true - tf.reduce_mean(y_true)))
    return (1 - SS_res/(SS_tot + tf.keras.backend.epsilon()))

def augment_data(data, columns, multiplier=2, noise_level=0.015):
    augmented_list = [data]
    for _ in range(multiplier):
        df_noise = data.copy()
        for col in columns:
            std = data[col].std()
            noise = np.random.normal(0, std*noise_level, size=len(data))
            df_noise[col] = df_noise[col] + noise
        augmented_list.append(df_noise)
    return pd.concat(augmented_list, ignore_index=True)

csv_path = r"C:\Users\acer_\Downloads\Nilai_Piksel.csv"
poly_path = r"C:\mYdata\SKRRP\Belajar\Pengolahan_Citra_Multispektral\program_pengolahan_citra\core\scaler\water_regression_polynom.joblib"
scaler_path = r"C:\mYdata\SKRRP\Belajar\Pengolahan_Citra_Multispektral\program_pengolahan_citra\core\scaler\water_regression_scaler.joblib"
model_path = r"C:\mYdata\SKRRP\Belajar\Pengolahan_Citra_Multispektral\program_pengolahan_citra\core\models\water_regression_model.h5"
df = pd.read_csv(csv_path)
X_col = ["M_GREEN", "M_RED", "NDVI", "NDRE", "GNDVI", "EVI", "VIDVI", "CIVE"] 
X_ = df[X_col]
Y_ = df["Status"]

# Fitur polinom 
poly = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
scaler = StandardScaler()
X_poly = poly.fit_transform(X_)
X_poly_cols = poly.get_feature_names_out(X_col)
joblib.dump(poly, poly_path)
print("Berhasil menyimpan polynom!")
df_poly = pd.DataFrame(X_poly, columns=X_poly_cols)
df_poly["Status"] = Y_.values

df_aug = augment_data(df_poly, X_poly_cols, multiplier=2)
X = df_aug[X_poly_cols]
y = df_aug["Status"]

X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

joblib.dump(scaler, scaler_path)
print("Berhasil menyimpan scaler!")

model = tf.keras.models.Sequential([
    tf.keras.layers.Dense(1024, input_shape=(len(X_poly_cols),),kernel_initializer="he_uniform"),
    tf.keras.layers.GaussianNoise(0.01),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Activation("swish"),
    tf.keras.layers.Dropout(0.04),

    tf.keras.layers.Dense(512, kernel_initializer="he_uniform"),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Activation("swish"),
    tf.keras.layers.Dropout(0.3),

    tf.keras.layers.Dense(256, activation="swish"),
    tf.keras.layers.Dense(128, activation="swish"),

    tf.keras.layers.Dense(1, activation="linear")
])

model.compile(
    optimizer=tf.keras.optimizers.Nadam(0.001),
    loss="huber", 
    metrics=["mae", r_square_metric]
)

callbacks = [
    tf.keras.callbacks.ModelCheckpoint(model_path, monitor="val_loss", save_best_only=True, verbose=0),
    tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=70, restore_best_weights=True),
    tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.2, patience=15, min_lr=1e-7, verbose=1)
]

print(">>> Memulai pelatihan")
history = model.fit(
    X_train_scaled,
    y_train,
    validation_data=(X_val_scaled, y_val),
    epochs=1000,
    batch_size=64,
    callbacks=callbacks,
    verbose=1
)

model = tf.keras.models.load_model(model_path, custom_objects={'r_square_metric':r_square_metric})
y_pred_test = np.clip(model.predict(X_test_scaled).flatten(), 0, 0.6)
r2_final = r2_score(y_test, y_pred_test)
mae_final = mean_absolute_error(y_test, y_pred_test)

print("\n" + "="*30)
print(f"HASIL AKHIR R2: {r2_final:.4f}")
print(f"HASIL AKHIR MAE: {mae_final:.4f}")