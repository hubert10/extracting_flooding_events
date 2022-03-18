import geopandas as gpd
import pandas as pd
import os
from rasterstats import zonal_stats
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = BASE_DIR + "/"
os.chdir(PROJECT_ROOT)

region = "dagana"
path_img = PROJECT_ROOT + region


# ==========================================================================
# ==========================================================================
mndwi_path = path_img + "/2022/mndwi"
boundary_path = path_img + "/boundaries/dagana2.geojson"
s2cloudless_path = path_img + "/2022/cloud"
reference_image_path = path_img + "/2022/mndwi/mndwi_2022-01-02.tif"
rgb_img = path_img + "/2022/rgb/rgb_2022-01-02.tif"
dir_name = s2cloudless_path

empty_array = path_img + "/output/test.tif"

grid_path = path_img + "/boundaries/grid52_dagana.geojson"

# Generate the flooding df and the proportion df


def create_flooding_prop_df(
    img,
    empty_array,
    grid_path,
    listcloud,
    flooding_path,
    proportion_path,
    savefile=True,
):

    # ===========================================================================
    # Populate the grid boundary with the flooding area
    # ==========================================================================
    date_list = [img_name.split("_")[1].split(".")[0] for img_name in listcloud]
    dates = {}
    c = 2
    dates[0] = "no-data"
    dates[1] = "no-flooding"
    for d in date_list:
        dates[c] = d
        c += 1
    count_ref_img1 = zonal_stats(grid_path, img, categorical=True, category_map=dates)
    stat_df = pd.DataFrame(count_ref_img1)
    stat_df = stat_df.fillna(0)

    # ===================================================================
    # Sort the dates
    # ==================================================================
    def sort_dates(dates_str, format="%Y-%m-%d"):
        # Sort data
        dates_obj = [
            datetime.strptime(date_time_str, format) for date_time_str in dates_str
        ]
        #  sorteddates = [datetime.strftime(ts, format) for ts in dates_obj]
        dates_obj.sort()
        return dates_obj

    date_str = sort_dates(stat_df.columns.to_list()[2:], format="%Y-%m-%d")
    dates_st = [d.strftime("%Y-%m-%d") for d in date_str]

    # ========================================== ==============================
    # Fill the df with the area size
    # =========================================================================
    count_ref_img0 = zonal_stats(
        grid_path, empty_array, categorical=True, category_map={1: "count"}
    )
    georead1 = gpd.read_file(grid_path)
    size = pd.DataFrame(count_ref_img0)
    size.fillna(0)
    size = size["count"]

    df = georead1.copy()
    df[dates_st] = stat_df[dates_st]
    df["total_area"] = size
    # ==========================================================================
    # Generate the  exploitable surface by remove water ways from the total area
    # ==========================================================================
    # don t consider this
    # df['farm_area'] = df['total_area'] - df[ dates_st [0]]

    # =====================================================================
    # generate cumulative flooding area
    # ======================================================================
    df_flooding = df.copy()
    list_ = dates_st[1:]
    for i in range(len(list_)):
        df_flooding[list_[i]] = df_flooding[list_[i - 1]] + df_flooding[list_[i]]

    # =====================================================================
    # generate proportion
    # ======================================================================
    df_prop = df_flooding.copy()
    list_ = dates_st[1:]
    for i in range(len(list_)):
        df_prop[list_[i]] = df_flooding[list_[i]] / df_prop["total_area"]

    # df_prop['farm_area'] =  df_prop['farm_area'] *100*0.0001
    df_prop["total_area"] = df_prop["total_area"] * 100 * 0.0001
    df_prop[dates_st[0]] = df_prop[dates_st[0]] * 100 * 0.0001

    df_prop = df_prop.rename(columns={dates_st[0]: dates_st[0] + "_standing water"})

    df_prop.to_csv(proportion_path)

    # =====================================================================
    # Determine the flooding date
    # ======================================================================
    maxValueIndex1 = df[dates_st[1:]].idxmax(axis=1)
    maxValues = df[dates_st[1:]].max(axis=1)
    df_flooding["flooding_date"] = maxValueIndex1

    df_flooding[dates_st] = df_flooding[dates_st] * 100 * 0.0001
    # df_flooding['farm_area'] = df_flooding['farm_area'] *100*0.0001
    df_flooding["total_area"] = df_flooding["total_area"] * 100 * 0.0001
    df_flooding["total_flooded_area"] = df[dates_st[1:]].sum(axis=1) * 100 * 0.0001
    # Rename the first acquisition date image
    df_flooding = df_flooding.rename(
        columns={dates_st[0]: dates_st[0] + "_standing water"}
    )

    if savefile == True:
        df_flooding.to_csv(flooding_path)

    df.to_csv()
    return df_flooding, df_prop


# Generate the time series of strength

count_ref_img0 = zonal_stats(
    grid_path, empty_array, categorical=True, category_map={1: "count"}
)
size = pd.DataFrame(count_ref_img0)
size.fillna(0)
size = size["count"]


def generate_performance(
    listcloud,
    grid_path,
    path_=path_img + "/2022/cloud/",
    save_to=path_img + "/2022/output/files/timeseries2022_n.csv",
):
    # ============================================================
    # Populate the grid with the size
    # ===========================================================
    count_ref_img0 = zonal_stats(grid_path, path_ + listcloud[0])
    georead1 = gpd.read_file(grid_path)
    df = georead1.copy()
    size = pd.DataFrame(count_ref_img0)["count"]
    df["total_area"] = size

    # ==================================================
    for img_name in listcloud:
        date = img_name.split("_")[1].split(".")[0]
        pim = path_ + img_name
        count_ref_img1 = zonal_stats(grid_path, pim, categorical=True)
        stat_df = pd.DataFrame(count_ref_img1)
        stat_df = stat_df.fillna(0)
        thresh = [i for i in stat_df.columns.to_list() if i < 40]
        df[date] = stat_df[thresh].sum(axis=1)

    # ==================== GENERATE THE PROPORTION #====================

    dates = [img_name.split("_")[1].split(".")[0] for img_name in listcloud[1:]]

    df1 = georead1.copy()
    df1["total_area"] = size
    # df1['farm_area'] = df1['total_area'] - list_standing_water
    # populate df1 with the total area
    for d in dates:
        df1[d] = df1["total_area"]
    df1[dates] = df[dates] / df1[dates] * 100
    df1["total_area"] = df1["total_area"] * 100 * 0.0001
    # df1['total_area'] = df1['total_area'] *100*0.0001

    df1 = df1.rename(columns={dates[0]: dates[0] + "_standing water"})
    df1.to_csv(save_to)
    return df1


# =================================================================================================
#                       UPDATE
# ==============================================================================================
def generate_performance_up(
    listcloud,
    empty_array,
    grid_path,
    cloud_probability_threshold=40,
    path_=path_img + "/2022/cloud/",
    save_to=path_img + "/2022/output/files/timeseries2022_n.csv",
):
    # ============================================================
    # Populate the grid with the size
    # ===========================================================
    # ========================================== ==============================
    # Fill the df with the area size
    # =========================================================================
    count_ref_img0 = zonal_stats(
        grid_path, empty_array, categorical=True, category_map={1: "count"}
    )
    georead1 = gpd.read_file(grid_path)
    size = pd.DataFrame(count_ref_img0)
    size.fillna(0)
    size = size["count"]

    georead1 = gpd.read_file(grid_path)
    df = georead1.copy()
    # size = pd.DataFrame(count_ref_img0)['count']

    df["total_area"] = size
    # ==================================================
    for img_name in listcloud:
        date = img_name.split("_")[1].split(".")[0]
        pim = path_ + img_name
        count_ref_img1 = zonal_stats(grid_path, pim, categorical=True)
        stat_df = pd.DataFrame(count_ref_img1)
        stat_df = stat_df.fillna(0)
        # Select value greater than 0 as 0 is made of both the probability and the no-data
        threshold_ = [i for i in stat_df.columns.to_list() if i > 0]
        # Count the number of pixels in with value greater than 0
        df["count"] = stat_df[threshold_].sum(axis=1)
        # Find the number of pixel with probability 0
        df["diff"] = df["total_area"] - df["count"]
        res_ = []
        for val in df["diff"].to_list():
            tmp = 0
            if val < 0:  # Number of pixel with 0 > total_area
                tmp = abs(val)
            if val > 0:  #
                tmp = 0
            res_.append(tmp)
        # Get the real number of 0 that is the probability
        df["diff_up"] = res_
        # Define a new threshold
        threshold_up = [i for i in threshold_ if i < cloud_probability_threshold]

        df[date] = stat_df[threshold_up].sum(axis=1) + df["diff_up"]

    # =============================
    # Save the file generate FOR PERSONAL PURPOSE
    # =============================
    # df.to_file()

    # ====================GENERATE THE PROPORTION
    dates = [img_name.split("_")[1].split(".")[0] for img_name in listcloud[1:]]
    df1 = georead1.copy()
    df1["total_area"] = size
    # df1['farm_area'] = df1['total_area'] - list_standing_water
    # populate df1 with the total area
    for d in dates:
        df1[d] = df1["total_area"]
    df1[dates] = df[dates] / df1[dates] * 100
    df1["total_area"] = df1["total_area"] * 100 * 0.0001
    # df1['total_area'] = df1['total_area'] *100*0.0001

    df1 = df1.rename(columns={dates[0]: dates[0] + "_standing water"})
    df1.to_csv(save_to)
    return df1


# Compute proportion and flooding

# Get List of filenames
def get_list_of_files(dir_name):
    # create a list of file and sub directories
    # names in the given directory
    list_of_file = os.listdir(dir_name)
    all_files = list()
    # Iterate over all the entries
    for entry in list_of_file:
        # Create full path
        filename = entry.split("/")[-1]
        if filename.startswith("cloud"):
            all_files.append(filename)
    return all_files


listcloud22 = get_list_of_files(dir_name)


# ================
# flooding and proportion
# ==================

listcloud = listcloud22
img = path_img + "/output/flooding_maps_2022.tif"

reference_image_path = path_img + "/2022/mndwi/mndwi_2022-01-02.tif"
path_to_image21 = path_img + "/2022/cloud/cloud_2022-01-02.tif"
empty_array = path_img + "/output/test.tif"
grid_path = path_img + "/boundaries/grid52_dagana.geojson"

# grid_path = '/content/drive/WORK/SCIENTIFIC_OFFICER-ICRISAT/Biophysical folder/Glorie/2022_work/ANALYSIS_NDVI_vs_MNDWI/dagana_ndvi_ts.geojson'

flooding_path = path_img + "/ANALYSIS_NDVI_vs_MNDWI/flooded_area_dagana2022.csv"
proportion_path = path_img + "/ANALYSIS_NDVI_vs_MNDWI/proportion_dagana2022.csv"

# =================================================
# Generate proportion
# ====================================================
f22, p22 = create_flooding_prop_df(
    img, empty_array, grid_path, listcloud, flooding_path, proportion_path
)
# ========================================

f22.to_file(path_img + "/ANALYSIS_NDVI_vs_MNDWI/flooded_area_dagana2022.geojson")

p22.to_file(path_img + "/ANALYSIS_NDVI_vs_MNDWI/proportion_dagana2022.geojson")

print(f"Total Flooded Area:\n{f22.total_flooded_area.sum()}\n")
