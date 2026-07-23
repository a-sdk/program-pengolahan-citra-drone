from core.logic.modul_transformasi import proses_segmentasi

folder = r"C:\Users\acer_\Documents\laporan skrpsi\New folder\hst59"
gndvi = rf"{folder}/gndvi.tif"
ndrei = rf"{folder}/ndrei.tif"
ndvi = rf"{folder}/ndvi.tif"
savi = rf"{folder}/savi.tif"
proses_segmentasi(
    input_folder=f"{folder}/clip_result.tif",
    ndvi_path=savi,
    output_folder=f"{folder}/segmentasi baru",

)
print("cik atuh meni garing")