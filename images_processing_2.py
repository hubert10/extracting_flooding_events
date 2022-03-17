# import required libraries
import rasterio
import pylab
from rasterio import plot
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
from pyproj import CRS
import osr
import ogr
import gdal
import glob
from shapely.geometry import mapping
from rasterio.mask import mask
import numpy as np
import matplotlib
import math
import os
from rasterstats import zonal_stats
from datetime import datetime
import os
import logging
import sys
from os import environ

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = BASE_DIR + "/"
os.chdir(PROJECT_ROOT)

# Define Paths to Images downloaded in scrip 1 of the process

region = "dagana"
year = "2022"

path_img = PROJECT_ROOT + region


# ==========================================================================
# ==========================================================================

# Specify the path of the images
mndwi_path = path_img + "/2022/mndwi"
boundary_path = path_img + "/data/boundaries/dagana2.geojson"
s2cloudless_path = path_img + "/2022/cloud"
reference_image_path = path_img + "/2022/mndwi/mndwi_2022-01-02.tif"
rgb_img = path_img + "/2022/rgb/mndwi_2022-01-02.tif"
test_img = path_img + "/output/test.tif"
dir_name = s2cloudless_path
# reference_s2cloudless_path =path_img+'/2021/cloud/cloud_2021-01-02.tif'

# Get List of filemames
def get_list_of_files(dir_name):
    # create a list of file and sub directories
    # names in the given directory
    listOfFile = os.listdir(dir_name)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        filename = entry.split("/")[-1]
        if filename.startswith("cloud"):
            allFiles.append(filename)
    return allFiles

def is_image_good_to_work_with(reference_image_path, img_path, boundary_path):
    """
    Check if the image if good to work woth 
    """
    boolean = True
    count_ref_img = zonal_stats(boundary_path, reference_image_path)
    count_current_img = zonal_stats(boundary_path, img_path)
    ratio = count_ref_img[0]["count"] / count_current_img[0]["count"]
    # if the number of pixels in the new image is 2 times less than the one in the reference image
    if ratio > 2:
        boolean = False
    return boolean


def select_images(
    mndwi_path,
    boundary_path,
    reference_image_path=path_img + "/2022/mndwi/mndwi_2022-01-02.tif",
):
    list_mndwi = os.listdir(mndwi_path)
    selection_mndwi = []
    for img_name in list_mndwi:
        print(img_name)
        val = is_image_good_to_work_with(
            reference_image_path, mndwi_path + "/" + img_name, boundary_path
        )
        if val == True:
            # fill in with the image name at time x
            selection_mndwi.append(img_name)
    return selection_mndwi


def collect_images(
    boundary_path,
    mndwi_path,
    s2cloudless_path,
    reference_image_path=path_img + "/2022/mndwi/mndwi_2022-01-02.tif",
):
    def sort_dates(dates_str, format="%Y-%m-%d"):
        # Sort data
        dates_obj = [
            datetime.strptime(date_time_str, format) for date_time_str in dates_str
        ]
        #  sorteddates = [datetime.strftime(ts, format) for ts in dates_obj]
        dates_obj.sort()
        return dates_obj

    def check_if_date_in_(file, img_name):
        if file in img_name:
            return True
        else:
            return False

    res = select_images(mndwi_path, boundary_path, reference_image_path)
    dates_str = [img_name.split("_")[1].split(".")[0] for img_name in res]
    dates = sort_dates(dates_str, format="%Y-%m-%d")
    dates_str = [d.strftime("%Y-%m-%d") for d in dates]

    list_cloud = os.listdir(s2cloudless_path)
    selection_ndwi = {}
    selection_s2cloudless = {}
    for d in dates_str:
        selection_ndwi[d] = "mndwi_" + d + ".tif"
        if "cloud_" + d + ".tif" in list_cloud:
            selection_s2cloudless[d] = "cloud_" + d + ".tif"
        else:
            selection_s2cloudless[d] = -1
    check_s2cloudless = [
        d for d in selection_s2cloudless.keys() if selection_s2cloudless[d] == -1
    ]
    print(
        "==================== NUMBER OF IMAGES WITH NO CORRESPONDIND S2CLOUDLESS IMAGES  : ",
        len(check_s2cloudless),
        "DATES : ",
        check_s2cloudless,
    )
    return selection_ndwi, selection_s2cloudless


def init_array(rgb_array):
    working_array = rgb_array.copy()
    for i in range(0, rgb_array.shape[0]):
        for j in range(0, rgb_array.shape[1]):
            if rgb_array[i, j] > 0:
                working_array[i, j] = 1
            else:
                working_array[i, j] = 0
    return working_array


list_mndwi = os.listdir(mndwi_path)

print(f"List of mndwi images:\n{len(list_mndwi)}\n")


rgb_array = rasterio.open(rgb_img).read(1)
r = init_array(rgb_array)


selection_ndwi, selection_s2cloudless = collect_images(
    boundary_path, mndwi_path, s2cloudless_path, rgb_img
)
listimg = []
listcloud = []

for i in selection_ndwi.keys():
    listimg.append(selection_ndwi[i])
    listcloud.append(selection_s2cloudless[i])


listcloud = get_list_of_files(dir_name)

#  'cloud_2020-01-03.tif',
#  'cloud_2020-01-08.tif',
#  'cloud_2020-01-13.tif',
#  'cloud_2020-01-18.tif',
#  'cloud_2020-01-23.tif',
#  'cloud_2020-01-28.tif',
#  'cloud_2020-02-02.tif',
#  'cloud_2020-02-07.tif',
#  'cloud_2020-02-12.tif',
#  'cloud_2020-02-17.tif',
#  'cloud_2020-02-22.tif',
#  'cloud_2020-02-27.tif',
#  'cloud_2020-03-03.tif',
#  'cloud_2020-03-08.tif',
#  'cloud_2020-03-13.tif',
#  'cloud_2020-03-18.tif',
#  'cloud_2020-03-23.tif',
#  'cloud_2020-03-28.tif',
#  'cloud_2020-04-02.tif',
#  'cloud_2020-04-07.tif',
#  'cloud_2020-04-12.tif',
#  'cloud_2020-04-17.tif',
#  'cloud_2020-04-22.tif',
#  'cloud_2020-04-27.tif',
#  'cloud_2020-05-02.tif',
#  'cloud_2020-05-07.tif',
#  'cloud_2020-05-12.tif',
#  'cloud_2020-05-17.tif',
#  'cloud_2020-05-22.tif',
#  'cloud_2020-05-27.tif']

# r = rasterio.open(path_img+'/2021/output/maps/test.tif').read(1)
r = rasterio.open(test_img).read(1)

arrayimgcopy = r.copy()
arraycloud = r.copy()
arrayimg3copy = r.copy()

arrayimg1 = arrayimgcopy.copy()
arrayimg11 = arrayimgcopy.copy()
arrayimg12 = arrayimgcopy.copy()
arrayimg13 = arrayimgcopy.copy()
arrayimg14 = arrayimgcopy.copy()
arraycloud1 = arrayimgcopy.copy()
arraycloud2 = arrayimgcopy.copy()
arrayimg15 = arrayimgcopy.copy()

arrayimg2 = arrayimgcopy.copy()
arraycloud = arrayimgcopy.copy()
arraytotalcloud = arrayimgcopy.copy()
arrayimg3 = arrayimg3copy.copy()


pix = 2
q = 2
inc = 0
fill = 2
fill2 = 3
fillneg = 13

while inc < len(listimg):
    g = listimg[inc]
    h = listcloud[inc]  # listrgb[inc]
    if (
        h != -1
    ):  # Soit tu utilises l image telquell, soit tu la   : Ca doit etre exceptionele
        print("---------- FIRST TRY --------------")
        print(inc)
        print("---------- END TRY ----------------")

        im1 = rasterio.open(mndwi_path + "/" + g, driver="Gtiff").read(1)
        im2 = rasterio.open(s2cloudless_path + "/" + h, driver="Gtiff").read(1)

        for i in range(0, im1.shape[0]):
            for j in range(0, im1.shape[1]):
                if q > 3:  #   arraytotalcloud[i,j] = q

                    if arrayimg1[i - 1, j - 1] == q - 1:
                        if im1[i, j] <= 0:
                            arrayimg11[i, j] = 5
                            arraycloud1[i - 1, j - 1] = pix
                            arrayimg1[i - 1, j - 1] = 1

                    if arrayimg12[i - 1, j - 1] == q - 1:
                        if im1[i, j] <= 0:
                            arraycloud2[i - 1, j - 1] = pix
                            arrayimg12[
                                i - 1, j - 1
                            ] = 1  # just here  # Probaby the best one
                if q > 2:
                    if arrayimg1[i - 1, j - 1] == q - 1:
                        if im1[i, j] <= 0:
                            arrayimg15[i, j] = 1

                if im1[i, j] > 0:  # Water is detected

                    if arrayimg1[i, j] == 1:  # The pixel is not yet filled
                        # ----------------------CASE 1
                        if q == 2:
                            arrayimg1[i, j] = q
                            # arrayimg13 [i,j] =  q  # just here
                        else:
                            # if cloud
                            if im2[i, j] < 40:  # == 255:
                                arrayimg1[i, j] = q
                                # arrayimg12 [i,j] = q

                    # CASE 2===================================
                    if arrayimg12[i, j] == 1:  # The pixel is not yet filled
                        # if cloud
                        if im2[i, j] < 40:  # == 255:
                            arrayimg12[i, j] = q

                    # CASE 3===================================
                    if arrayimg13[i, j] == 1:  # The pixel is not yet filled  ONLY HERE
                        # skip water img
                        if q == 2:
                            arrayimg13[i, j] = 2
                            # arrayimg13 [i,j] =  q  # just here
                        else:
                            # if cloud
                            if im2[i, j] < 40:  # == 255:
                                # arrayimg1[i,j] = q
                                arrayimg13[i, j] = q

                    # CASE 4===================================               No condition here
                    if arrayimg14[i, j] == 1:  # The pixel is not yet filled
                        # if cloud
                        if im2[i, j] < 40:  # == 255:
                            # arrayimg1[i,j] = q
                            arrayimg14[i, j] = q

        q = q + 1
        inc += 1
        pix += 1

    # ==================== compute res =========================

profile = rasterio.open(reference_image_path, driver="Gtiff").profile
with rasterio.open(path_img + "/output/flooding_maps_2022.tif", "w", **profile) as dst:
    dst.write(arrayimg14.astype(rasterio.uint8), 1)

res_set3 = list(set(i for j in arrayimg14 for i in j))
area = []
val = {}
for w in res_set3:
    x = arrayimg14[arrayimg14 == w]
    l = x.size * 100 * 0.0001
    area.append(l)
    val[w] = l
val

sum(area) - area[0] - area[1] - area[2]
