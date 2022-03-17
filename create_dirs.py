import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = BASE_DIR + "/"

region = "dagana"
year = "2022"


def create_directories(data_dir, region, year):
    # Folder where data for running the notebook is stored
    DATA_FOLDER = os.path.join(data_dir, region)
    subfolder_names = [str(year), "data", "output"]
    for subfolder_name in subfolder_names:
        os.makedirs(os.path.join(DATA_FOLDER, subfolder_name), exist_ok=True)
        if subfolder_name == "data":
            os.makedirs(os.path.join(DATA_FOLDER, "boundaries"), exist_ok=True)

    # Locations for collected data and results
    DATASET_FOLDER = os.path.join(data_dir, region, year)
    subfolder_names = ["mndwi", "cloud", "rgb"]
    for subfolder_name in subfolder_names:
        os.makedirs(os.path.join(DATASET_FOLDER, subfolder_name), exist_ok=True)
    print("Required directories successfully created")


create_directories(PROJECT_ROOT, region, year)
