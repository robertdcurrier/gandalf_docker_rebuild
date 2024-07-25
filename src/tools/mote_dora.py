#!/usr/bin/env python3
"""
"""
import json
import random
import sys
import os
import requests
import cmocean
import gsw
import gc
import logging
import time
import wget
import glob
import numpy as np
import pandas as pd
import seawater as sw
import plotly.express as px
import matplotlib.pyplot as plt
import datetime
from datetime import date
from datetime import timedelta
from matplotlib import dates as mpd
from decimal import getcontext, Decimal
from calendar import timegm
from geojson import LineString, FeatureCollection, Feature, Point
from pandas.plotting import register_matplotlib_converters
from pymongo import MongoClient
from pymongo import errors

# THESE SETTINGS NEED TO COME FROM CONFIG FILE EVENTUALLY
# END GLOBALS



def dora_surface_marker(df):
    """
    """
    logging.info(f'dora_surface_marker(): {len(df)} records')

    logging.info('dora_surface_marker(): creating surface marker')
    coords = []
    features = []
    today = datetime.datetime.today()
    for index, row in df.iterrows():
        point = Point([row['Predicted Longitude'], row['Predicted Latitude']])
        coords.append(point)
        surf_marker = Feature(geometry=point, id='surf_marker')
        features.append(surf_marker)
    df = df.sort_values(by=['UTC Time'], ascending=False)

    logging.debug("dora_surface_marker(): Generating track")
    track = LineString(coords)
    track = Feature(geometry=track, id='track')
    features.append(track)

    return FeatureCollection(features)


def write_geojson_file(data):
    """
    Created: 2020-06-05
    Modified: 2020-10-26
    Author: robertdcurrier@gmail.com
    Notes: writes out feature collection
    """
    fname = ("/data/gandalf/deployments/geojson/dora.json")
    logging.warning("write_geojson(): Writing %s" % fname)
    outf = open(fname,'w')
    outf.write(str(data))
    outf.close()


def dora_process():
    """
    Created: 2024-01-23
    Modified: 2024-01-23
    Author: robertdcurrier@gmail.com
    Notes: Main entry point. We now plot both 2D and 3D dora data
    """

    df = pd.read_csv('predictions.csv')
    dora_features = dora_surface_marker(df)
    write_geojson_file(dora_features)



if __name__ == '__main__':
    # Need to add argparse so we can do singles without editing...
    logging.basicConfig(level=logging.INFO)
    start_time = time.time()
    dora_process()
    end_time = time.time()
    minutes = ((end_time - start_time) / 60)
    logging.warning('Duration: %0.2f minutes' % minutes)
