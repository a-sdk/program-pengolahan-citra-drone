import rasterio as rio
from rasterio.windows import Window

def jalan(input_folder):
    with rio.open(input_folder) as src:
        base_profile = src.profile
        total_window = Window(0, 0, src.width, src.height)
        print(total_window)
        for ji, window in src.block_windows(1):
            print(f"Window {window}")


if __name__ == "__main__":
    path = r"C:\Users\acer_\Documents\Orthomosaic\tes aplikasi\hasil_potong.tif"
    jalan(path)