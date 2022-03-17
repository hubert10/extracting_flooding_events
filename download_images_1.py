# -*- coding: utf-8 -*-
"""Remote Sensing  Predictables  - Classification V1.03

Created on March 16 at Manobi Africa Dakar 10:34:42 2022

@authors: Pierre C. Traore - ICRISAT/ Manobi Africa
          Hubert Kanyamahanga - ICRISAT/ Manobi Africa
          Glorie Wowo - - ICRISAT/ Manobi Africa
"""
################################################################################
########################### Introduction  ######################################
################################################################################

"""
This notebook shows you how to extract floading events using MNDWI, CLOUD Prob and RGB image. The images 
extractions is handled  with Earth Engine resources. 
The general workflow for floading extraction is:
"""
#####0. Environment Setup
#####1. Collect training data. Assemble features which have a property that
#######stores the known class label and properties storing numeric values for the predictors.
#####2. Instantiate a classifier. Set its parameters if necessary.
#####3. Train the classifier using the training data.

################################################################################
####################### Install and load packages ##############################
################################################################################

""" if you are working with Colab, this packages will require to be installed every time the 
script is run. If runnning from a local machine this can be commented out/deleted
"""
# Create a virtualenv and install all these packages and then you are ready to go
# pip install geemap,
# pip install ipygee
# pip install geopandas
# pip install js2py
# pip install folium
# pip install rasterio
# pip install tslearn
# pip install earthengine-api

# Import os packages
import os, ee, json, subprocess
import ipygee as ui
from os import path as op
from datetime import datetime

# Pandas modules to interact with spatial data
import geopandas as gpd
import pandas as pd
import numpy as np
from functools import reduce


# Login into GEE
ee.Authenticate()
ee.Initialize()

# Functions definitions


class generate_image(object):
    def __init__(
        self,
        api,
        boundaries_path,
        start_date,
        end_date,
        cloud_percentage,
        folder="earthengine",
    ):
        self.api = api
        self.boundaries_path = boundaries_path
        self.start_date = start_date
        self.end_date = end_date
        self.cloud_percentage = cloud_percentage
        # self.filename = filename
        self.folder = folder

    def get_geometry(self):
        area = self.api.FeatureCollection(self.boundaries_path)
        return area.geometry()

    def get_image(self):
        s2 = self.api.ImageCollection("COPERNICUS/S2_SR")
        geometry = self.get_geometry()
        filtered = (
            s2.filter(
                self.api.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", self.cloud_percentage)
            )
            .filter(self.api.Filter.date(self.start_date, self.end_date))
            .filter(self.api.Filter.bounds(geometry))
        )
        image = filtered.median()
        return image

    def get_images(self):
        s2 = self.api.ImageCollection("COPERNICUS/S2_SR")
        geometry = self.get_geometry()
        filtered = (
            s2.filter(
                self.api.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", self.cloud_percentage)
            )
            .filter(self.api.Filter.date(self.start_date, self.end_date))
            .filter(self.api.Filter.bounds(geometry))
        )
        return filtered

    # Create a composite and apply cloud mask
    def get_mask_images(self):
        # Cloud masking
        def maskCloudAndShadows(image):
            cloudProb = image.select("MSK_CLDPRB")
            snowProb = image.select("MSK_SNWPRB")
            cloud = cloudProb.lt(40)
            snow = snowProb.lt(5)
            scl = image.select("SCL")
            # shadow = scl.eq(3); # 3 = cloud shadow
            # cirrus = scl.eq(30); # 10 = cirrus
            # Cloud probability less than 5% or cloud shadow classification
            mask = cloud.And(snow)  # .And(cirrus.neq(1)).And(shadow.neq(1))
            return image.updateMask(mask)

        s2 = self.api.ImageCollection("COPERNICUS/S2_SR")
        geometry = self.get_geometry()
        filtered = (
            s2.filter(
                self.api.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", self.cloud_percentage)
            )
            .filter(self.api.Filter.date(self.start_date, self.end_date))
            .map(maskCloudAndShadows)
            .filter(self.api.Filter.bounds(geometry))
        )
        return filtered

    # --------------------------------------------

    def get_s2_cloudless(self):
        s2_cloudless_col = (
            self.api.ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY")
            .filterBounds(self.get_geometry())
            .filterDate(self.start_date, self.end_date)
        )
        return s2_cloudless_col

    def mosaic_by_date(self, imgCol):
        """
        mosaic_by_date is a function that merges images together that have the same date.

        @ imgCol: [ee.ImageCollection] mandatory value that specifies the image collection to merge by dates with.

        Returns ee.ImageCollection
        """
        # Convert the image collection to a list.
        imgList = imgCol.toList(imgCol.size())

        # Driver function for mapping the unique dates
        def uniqueDriver(image):
            return self.api.Image(image).date().format("YYYY-MM-dd")

        uniqueDates = imgList.map(uniqueDriver).distinct()

        # Driver function for mapping the moasiacs
        def mosaicDriver(date):
            date = self.api.Date(date)

            image = imgCol.filterDate(date, date.advance(1, "day")).mosaic()

            return image.set(
                "system:time_start",
                date.millis(),
                "system:id",
                date.format("YYYY-MM-dd"),
            )

        mosaicImgList = uniqueDates.map(mosaicDriver)

        return self.api.ImageCollection(mosaicImgList)

    def get_task(self, image, filename):
        aoi = self.get_geometry()
        task = self.api.batch.Export.image.toDrive(
            **{
                "image": image,
                "description": filename,
                "folder": self.folder,
                "fileNamePrefix": filename,
                "region": aoi,
                "scale": 10,
                "maxPixels": 1e12,
                "fileFormat": "GeoTIFF",
            }
        )
        return task

    def get_ndvi_task(self, ndvi_name, image=False):
        # print(ndvi_name)
        ndvi_name = (
            ndvi_name
            + "ndvi_"
            + self.start_date
            + "to"
            + self.end_date
            + "_cloudval-"
            + str(self.cloud_percentage)
        )
        print(ndvi_name)
        geometry = self.get_geometry()
        # print('geometry')
        # print(geometry)
        if image == False:
            image = self.get_image()
        else:
            image = image
        # print('image')
        # print(image)
        ndvi = image.normalizedDifference(["B8", "B4"]).rename(["ndvi"])
        # print(ndvi)
        visualized_ndvi = ndvi.clip(geometry)
        # print(visualized_ndvi)

        # task = self.api.batch.Export.image.toDrive(
        #   **{
        #             'image': visualized_ndvi,
        #             'description':ndvi_name,
        #             'folder': self.folder,
        #             'fileNamePrefix':ndvi_name,
        #              'region': geometry,
        #              'scale': 10,
        #              'maxPixels': 1e12,
        #              'fileFormat': "GeoTIFF",
        #     }
        #   )
        task = self.get_task(visualized_ndvi, ndvi_name)
        return task

    def get_mndwi_task(self, mndwi_name, image=False):
        mndwi_name = mndwi_name  # +'_mndwi_' #+ self.start_date+'to'+ self.end_date +'_cloudval-'+ str(self.cloud_percentage)
        geometry = self.get_geometry()
        if image == False:
            image = self.get_image()
        else:
            image = image
        mndwiVis = {"min": 0, "max": 0.5, "palette": ["white", "blue"]}
        mndwi = image.normalizedDifference(["B3", "B11"]).rename(["mndwi"])
        visualized_mndwi = mndwi.clip(geometry)
        # task = self.api.batch.Export.image.toDrive(
        #   **{
        #             'image': visualized_mndwi,
        #             'description':mndwi_name,
        #             'folder': self.folder,
        #             'fileNamePrefix': mndwi_name,
        #              'region': geometry,
        #              'scale': 10,
        #              'maxPixels': 1e12,
        #              'fileFormat': "GeoTIFF",
        #     }
        #   )
        # color_mndwi = mndwi.clip(geometry).visualize(**mndwiVis);

        # task = self.get_task(color_mndwi ,mndwi_name)
        task = self.get_task(visualized_mndwi, mndwi_name)
        return task

    def get_ndwi_task(self, ndwi_name, image=False):
        ndwi_name = (
            ndwi_name
            + "ndwi_"
            + self.start_date
            + "to"
            + self.end_date
            + "_cloudval-"
            + str(self.cloud_percentage)
        )
        geometry = self.get_geometry()
        if image == False:
            image = self.get_image()
        else:
            image = image
        ndwi = image.normalizedDifference(["B8", "B11"]).rename(["ndwi"])
        visualized_ndwi = ndwi.clip(geometry)
        # task = self.api.batch.Export.image.toDrive(
        #   **{
        #             'image': visualized_ndwi,
        #             'description':ndwi_name,
        #             'folder': self.folder,
        #             'fileNamePrefix': ndwi_name,
        #              'region': geometry,
        #              'scale': 10,
        #              'maxPixels': 1e12,
        #              'fileFormat': "GeoTIFF",
        #     }
        #   )
        task = self.get_task(visualized_ndwi, ndwi_name)
        return task

    def get_rgb_img_task(self, rgb_name, image=False):
        rgb_name = rgb_name  # + 'rgb_' +self.start_date+'to'+ self.end_date +'_cloudval-'+ str(self.cloud_percentage)
        geometry = self.get_geometry()
        if image == False:
            image = self.get_image()  # .select(['B4', 'B3', 'B2'])
        else:
            image = image
        rgbVis = {"min": 0.0, "max": 3000, "bands": ["B4", "B3", "B2"]}
        # Map.addLayer(image, rgbVis, 'Filtered Collection');
        # Map.addLayer(image.clip(geometry), rgbVis, 'Image')
        visualized_rgb = image.clip(geometry).visualize(**rgbVis)
        # .visualize(image)
        # task = self.api.batch.Export.image.toDrive(
        #   **{
        #   'image': visualized_rgb,
        #   'description':rgb_name,
        #   'folder': 'earthengine',
        #   'fileNamePrefix':rgb_name,
        #   'region': geometry,
        #   'scale': 10,
        #   'maxPixels': 1e12,
        #   'fileFormat': "GeoTIFF",
        #     }
        #   )
        task1 = self.get_task(visualized_rgb, rgb_name)

        return task1

    # ==================================================================================
    # ==================================================================================

    def add_cloud_bands(self, img):
        CLD_PRB_THRESH = 60
        # Get s2cloudless image, subset the probability band.
        cld_prb = self.api.Image(img.get("s2cloudless")).select("probability")

        # Condition s2cloudless by the probability threshold value.
        is_cloud = cld_prb.gt(CLD_PRB_THRESH).rename("clouds")

        # Add the cloud probability layer and cloud mask as image bands.
        return img.addBands(self.api.Image([cld_prb, is_cloud]))

    def get_s2_cloudless_task(self, cloud_name, image=False):
        geometry = self.get_geometry()
        if image == False:
            image = self.get_image()  # .select(['B4', 'B3', 'B2'])
        else:
            image = image
        # tmp =cloud_name.split('_')[1].split('-')
        # START_DATE= tmp[0] +  tmp[1] +  tmp[2]+str(1)
        # END_DATE = tmp[0] +  tmp[1] + tmp[2]+str(2)

        # img = self.getcloud_images(START_DATE, END_DATE)

        # img = img.mosaic()

        # cloud_img = image.clip(geometry).visualize(  **{ 'min': 0.0,'max': 100, 'palette':['brown', 'gray' ,'white']} )
        cloud_img = image.clip(geometry)

        task = self.get_task(cloud_img, cloud_name)
        return task

    def get_all_mosaic(self, types=["mndwi", "rgb", "cloud"], mask=False):
        if mask == False:
            collection = self.mosaic_by_date(self.get_images())
            # get s2cloudless images
            error = False
            try:
                collection_s2cloudless = self.mosaic_by_date(self.get_s2_cloudless())
                image_lists2cloudless = collection_s2cloudless.toList(
                    collection_s2cloudless.size()
                )
            except:
                error = True
                print(error)
            print("error", error)
            image_list = collection.toList(collection.size())
            img_size = image_list.size().getInfo()
            print("size collection", image_list.size().getInfo())
            print("error", error)
            print(
                "size collection  s2cloudless", image_lists2cloudless.size().getInfo()
            )

            # unique_dates =  ee.Image(image_list .get(2)).date().format("YYYY-MM-dd")
            # print('datename',unique_dates.getInfo())
            tasks = []
            for i in range(img_size):
                single_img = self.api.ImageCollection(
                    [image_list.get(i), image_list.get(i)]
                ).mosaic()

                date = (
                    self.api.Image(image_list.get(i))
                    .date()
                    .format("YYYY-MM-dd")
                    .getInfo()
                )
                if "rgb" in types:
                    tasks.append(self.get_rgb_img_task("rgb_" + str(date), single_img))
                if "mndwi" in types:
                    tasks.append(self.get_mndwi_task("mndwi_" + str(date), single_img))
                if "cloud" in types:
                    img = self.api.ImageCollection(
                        [image_lists2cloudless.get(i), image_lists2cloudless.get(i)]
                    ).mosaic()
                    tasks.append(self.get_s2_cloudless_task("cloud_" + str(date), img))
                if "swi" in types:
                    tasks.append(self.getSWI_task("swi_" + str(date), single_img))

            return tasks
        # =================================================================================

        else:  # GET IMAGES WITH MASK  PIXELS
            collection = self.mosaic_by_date(self.get_mask_images())
            # get s2cloudless images
            error = False
            collection_s2cloudless = self.mosaic_by_date(self.get_s2_cloudless())

            image_list = collection.toList(collection.size())
            img_size = image_list.size().getInfo()
            print("size collection", image_list.size().getInfo())

            tasks = []
            for i in range(img_size):
                single_img = self.api.ImageCollection(
                    [image_list.get(i), image_list.get(i)]
                ).mosaic()
                date = (
                    self.api.Image(image_list.get(i))
                    .date()
                    .format("YYYY-MM-dd")
                    .getInfo()
                )
                if "rgb" in types:
                    tasks.append(self.get_rgb_img_task("rgb_" + str(date), single_img))
                if "mndwi" in types:
                    tasks.append(self.get_mndwi_task("mndwi_" + str(date), single_img))
            return tasks


################################# Get all images mosaic by dates #####################################

# set up your working paths

# Change the file paths to match the file locations in your Gee project.
# These tow files have to be uploaded in the GEE assets folder
api = ee
boundaries_path = "projects/ee-hubertkanye/assets/dagana"
start_date = "2022-01-01"
end_date = "2022-03-16"
cloud_percentage = 100
folder = "earthengine"
generate_im1 = generate_image(
    api, boundaries_path, start_date, end_date, cloud_percentage, folder
)

############### MNDWI Computation ################

# Get the mndwi images
tasks = generate_im1.get_all_mosaic(["mndwi"])
for tsk in tasks:
    tsk.start()


##################   CLOUD Computation #############

# Download the S2CLOUDLESS
tasks = generate_im1.get_all_mosaic(["cloud"])
for tsk in tasks:
    tsk.start()


##################   RGB Download #########################

# Download an rgb image
tasks = generate_im1.get_all_mosaic(["rgb"])
for tsk in tasks:
    tsk.start()
