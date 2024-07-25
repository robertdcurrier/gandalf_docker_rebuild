#!/usr/bin/env python3
"""
Name:       gandalf_csv_utils.py
Created:    2016-09-05
Modified:   2018-08-01
Author:     bob.currier@gcoos.org
pylint score: 10.0 out of 10.0 2016-09-06
"""
import sys
import os
import json
import geojson
import logging
import datetime
import glob
import pandas as pd
from natsort import natsorted
from datetime import date, time, timedelta
from decimal import getcontext, Decimal
from subprocess import Popen, PIPE
from haversine import haversine, Unit
logging.basicConfig(level=logging.WARNING)


def eez_early_warning(vehicle, last_pos):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2023-09-20
    Modified:   2023-09-20
    Notes:      Checks latest coordinates for each vehicle and alerts
                if distance to US EEZ border is < 50 miles. The distance
                threshold should be a config file setting.
    """
    eez_threshold = 50
    eez_dist = []
    eez = '/data/gandalf/deployments/geojson/gom-eez.json'
    logging.info('eez_early_warning(%s)', vehicle)
    data = geojson.load(open(eez))
    for feature in data['features']:
        coords = (feature['geometry']['coordinates'])
    for linestring in coords[0]:
        for pos in linestring:
            lat = pos[1]
            lon = pos[0]
            pos = [lat, lon]
            distance = haversine(pos, last_pos, unit=Unit.NAUTICAL_MILES)
            eez_dist.append(distance)
    dist = min(eez_dist)

    if (dist < eez_threshold):
        logging.warning("eez_early_warning(%s): EEZ WARNING %d", vehicle, dist)
        return True
    else:
        return False


def get_modcomp_path(config):
    """
    Author:     bob.currier@gcoos.org
    Created:    2023-09-15
    Modified:   2023-09-19
    Notes:      Uses vehicle name to build paths for each days model
                comp files on a per vehicle basis. For now we just
                use the 400m file as this always exists. The 1000m file
                is only for vehicles diving that deep, and will require
                additional work to integrate into the infobox popup.

                2023-09-18: Need to pull newest file for each vehicle
                based on timestamp. Trying to pull by name doesn't work
                as for whatever reason Rutgers doesn't generate files for
                all vehicles with both depths... it seems a little random, and
                rather than having blank 'PNG' in the InfoBox it is best to use
                the most recent file, so there will always be an image.

                2023-09-19: Removed f string formatting for png_glob as cron
                didn't like.

    """
    vehicle = config['gandalf']['vehicle']

    mod_comp_png_root = '/data/gandalf/deployments/model_comps/'
    png_glob = mod_comp_png_root + vehicle + "*.png"
    png_files = natsorted(glob.glob(png_glob))
    # Return most recent file
    try:
        png_file = (max(png_files, key = os.path.getctime))
    except:
        logging.info('get_modcomp_path(%s): No ModComp files found', vehicle)
        png_file = '/static/images/data_unavailable.webp'
        logging.info('using %s instead' % png_file)
        return png_file
    logging.warning('get_modcomp_path(%s): Using %s', vehicle, png_file)
    return png_file

