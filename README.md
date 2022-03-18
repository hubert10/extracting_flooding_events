# Extracting Flooding Events

What we are trying to do here is to extract flooded areas and proportions using MNDWI indixes, RGB images and CLOUD probability from Sentinel 2 imagery.

# Getting Started

The workflow is divided into 3 steps: 1. Downloading images from Google Earth Engine, 2. Pre-process the downloaded images, and then 3. extract flooded areas and their corresponding proportions

* [downalod_images.py](downalod_images.py) Is the easiest way to start. It shows how to download high resolution images fron Sent2

* [processing_images.py](processing_imaages.py) shows how to mosaic downloaded images and process them.

* ([extract_data.py](extract_data.py): This file contains the main of getting flooding dates and areas. 



