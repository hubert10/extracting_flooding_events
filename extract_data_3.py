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
boundary_path = path_img + "/data/boundaries/dagana2.geojson"
s2cloudless_path = path_img + "/2022/cloud"
reference_image_path = path_img + "/2022/mndwi/mndwi_2022-01-02.tif"
rgb_img = path_img + "/2022/rgb/mndwi_2022-01-02.tif"

empty_array = path_img + "/output/test.tif"

grid_path = path_img + "/data/boundaries/grid52_dagana.geojson"

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
