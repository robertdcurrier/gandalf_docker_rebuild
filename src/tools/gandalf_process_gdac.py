#!/usr/bin/env python3
"""
Name:       gandalf_harvest_gdac.py
Created:    2018-06-07
Modified:   2022-06-13
Author:     bob.currier@gcoos.org
Notes:      Harvests non-GANDALF gliders from GDAC ERRDAP server. Data returned
            as JSON text. We use the JSON to build a pandas DF. We create
            sensors.csv from the DF to support all further operations.
"""
import sys
import json
import time
from calendar import timegm
from datetime import datetime
from datetime import date
from datetime import timedelta
from matplotlib import dates as mpd
import requests
import itertools
import logging
import argparse
import pandas as pd
import numpy as np
from geojson import LineString, FeatureCollection, Feature, Point
from gandalf_utils import get_vehicle_config
from gandalf_utils_2 import get_modcomp_path
logging.basicConfig(level=logging.WARNING)


def slim_gdac_df(vehicle, data_frame):
    """
    Name:       slim_gdac_df
    Author:     bob.currier@gcoos.org
    Created:    2022-05-19
    Modified:   2022-06-06
    Notes:      Drops excessive lat/lons
    """
    config = get_vehicle_config(vehicle)

    data_frame.latitude = data_frame.latitude.round(6)
    data_frame.longitude = data_frame.longitude.round(6)
    slim_df = data_frame.drop_duplicates(['latitude'])
    slim_df = slim_df.drop_duplicates(['longitude'])
    slim_df = slim_df.dropna()
    # Start and End date/time
    start_date = (time.strftime("%Y-%m-%d",
                  time.strptime(config["trajectory_datetime"],
                                "%Y%m%dT%H%M")))
    return slim_df


def gandalf_gdac_track(vehicle):
    """
    Name:       gandalf_gdac_track
    Author:     robertdcurrier@gmail.com
    Created:    2022-06-07
    Modified:   2022-06-13
    Notes:      slim_df removes lat/lon dupes and gen_track makes a
                JSON fC track.
    """
    logging.warning('gandalf_gdac_track(%s)' % vehicle)
    fcoll = []
    coords = []
    features = []

    config = get_vehicle_config(vehicle)
    public_name = config['gandalf']['public_name']
    operator = config['gandalf']['operator']
    vehicle_type = config['gandalf']['vehicle_type']
    project = config['gandalf']['project']

    df1 = gdac_to_df(vehicle)
    slim_df = slim_gdac_df(vehicle, df1)
    # temp fix 2024-07-20
    bad_gliders = ['ng960','ng1116']
    lon_min = -83
    if vehicle in bad_gliders:
        slim_df = slim_df.loc[slim_df['longitude'] <= lon_min]

    for index, row in slim_df.iterrows():
        longitude = row['longitude']
        latitude = row['latitude']
        coords.append((longitude, latitude))

    track = LineString(coords)
    track = Feature(geometry=track, id='track')
    track.properties['style'] = (config['gandalf']['style'])

    features.append(track)
    last_pos = gen_last_pos(vehicle, slim_df)
    features.append(last_pos)
    return features

def get_gdac_json(vehicle):
    """
    Name:       get_gdac_json
    Author:     robertdcurrier@gmail.com
    Created:    2022-06-13
    Modified:   2022-06-13
    Notes:      Changed from using geoJSON to straight JSON. This allows us
                to read the JSON with pandas and create a df with sensor names
                used as column headers. The downloaded JSON file is the
                equivalent of Slocum SBD/TBD files as we use it to create
                sensors.csv for all other operations.
    """
    logging.warning('get_gdac_json(%s)' % vehicle)
    features = []
    logging.info("fetch_erddap(%s)" % vehicle)
    start_time = time.time()
    # get config info for each vehicle
    config = get_vehicle_config(vehicle)
    gdac_url = config["gandalf"]["gdac_url"]
    json_dir = config["gandalf"]["gdac_json_dir"]
    json_data = requests.get(gdac_url).text
    end_time = time.time()
    fetch_time = end_time - start_time
    logging.info('get_gdac_json(): Fetch took %0.2f seconds' % fetch_time)
    # We need to write json_data out so we don't have to refetch for plots
    fname = '%s/%s_gdac.json' % (json_dir, vehicle)
    json_file = open(fname, 'w+')
    logging.info('get_gdac_json(%s): Writing %s' % (vehicle, fname))
    json_file.write(json_data)
    json_file.close()


def gdac_to_df(vehicle):
    """
    Name:       gdac_to_df
    Author:     robertdcurrier@gmail.com
    Created:    2022-06-13
    Modified:   2022-06-13
    Notes:      Reads downloaded JSON file from GDAC and creates a panda DF
                using columnNames as headers
    """
    logging.warning('gdac_to_df(%s)'% (vehicle))
    config = get_vehicle_config(vehicle)
    json_dir = config["gandalf"]["gdac_json_dir"]
    json_file = "%s/%s_gdac.json" % (json_dir, vehicle)
    logging.info('gdac_to_df(%s) using %s'% (vehicle, json_file))
    try:
        df = pd.read_json(json_file)

    except Exception:
        logging.warning('gdac_to_df(): Could not read json file')
        return []
    try:
        df1 = (pd.DataFrame(df['table']['rows'],
               columns=df['table']['columnNames']))
    except Exception:
        logging.warning('gdac_to_df(): Failed to create DF1')
        return []

    slim_df = slim_gdac_df(vehicle, df1)
    logging.info('gdac_to_df(%s): Adding epoch column' % vehicle)
    for index, row in slim_df.iterrows():
        utc_time = time.strptime(row['time'], "%Y-%m-%dT%H:%M:%SZ")
        epoch = timegm(utc_time)
        slim_df.at[index,'epoch'] = epoch
    return slim_df


def gen_last_pos(vehicle, df):
    """
    Name:       gen_last_pos
    Author:     robertdcurrier@gmail.com
    Created:    2022-06-06
    Modified:   2022-06-13
    Notes:      Makes last pos html and icon.
                2022-06-13: Changed date format to follow Slocum convention
    """
    logging.warning('gen_last_pos(%s): making last_pos', vehicle)
    config = get_vehicle_config(vehicle)
    vehicle = config['gandalf']['vehicle']
    # Date math to calculate days_wet
    deploy_date = (time.strftime("%Y-%m-%d",
                                 time.strptime(config["trajectory_datetime"],
                                                "%Y%m%dT%H%M%S")))
    date_obj = datetime.strptime(deploy_date, "%Y-%m-%d").date()
    current_date = date.today()
    days_wet = (current_date - date_obj).days

    # get modcomp path
    mod_comp_path = get_modcomp_path(config)

    infobox_image = config["gandalf"]["infoBoxImage"]
    public_name = config['gandalf']['public_name']
    operator = config['gandalf']['operator']
    vehicle_model = config['gandalf']['vehicle_model']
    project = config['gandalf']['project']
    data_source = config["gandalf"]["data_source"]
    last_lon = df.iloc[-1]['longitude'].round(4)
    last_lat = df.iloc[-1]['latitude'].round(4)
    last_pos = Point((last_lon, last_lat))
    latitude = last_lat
    longitude = last_lon

    last_surfaced = df.iloc[-1]['time']
    ls = (datetime.strptime(last_surfaced,
                     '%Y-%m-%dT%H:%M:%SZ'))
    last_surfaced = ls.strftime("%Y-%m-%d %H:%M UTC")
    last_pos = Feature(geometry=last_pos, id='last_pos')
    last_pos.properties['vehicle'] = vehicle
    last_pos.properties['last_surfaced'] = last_surfaced
    last_pos.properties['latitude'] = last_lat
    last_pos.properties['longitude'] = last_lon
    last_pos.properties['days_wet'] = days_wet
    last_pos.properties['public_name'] = public_name
    last_pos.properties['data_source'] = data_source
    last_pos.properties['style'] = (config['gandalf']['style'])
    last_pos.properties['currPosIcon'] = (config['gandalf']['currPosIcon'])
    last_pos.properties['iconSize'] = (config['gandalf']['iconSize'])
    # HTML for InfoBox

    last_pos.properties['html'] = """
    <div class='infoBoxTitle'><span class='infoBoxTitle'>%s</span></div>
    <center><img src=%s></img></center>
    <hr>
    <div class='infoBoxHeading'><span class='infoBoxHeading'>Status</span></div>
    <table class='infoBoxTable'>
    <tr>
        <td class='td_infoBoxSensor'>Last Report:</td>
        <td class='td_infoBoxData'>%s</td>
    </tr>
    <tr>
        <td class='td_infoBoxSensor'>Operator:</td>
        <td class='td_infoBoxData'>%s</td>
    </tr>

    <tr>
        <td class='td_infoBoxSensor'>Vehicle Type:</td>
        <td class='td_infoBoxData'>%s</td>
    </tr>

    <tr>
        <td class='td_infoBoxSensor'>Project:</td>
        <td class='td_infoBoxData'>%s</td>
    </tr>
    <tr>
        <td class='td_infoBoxSensor'>Last Position:</td>
        <td class='td_infoBoxData'>%sW %sN</td>
    </tr>
    <tr>
        <td class='td_infoBoxSensor'>Data Source:</td>
        <td class='td_infoBoxData'>%s</a>
        </td>
    </tr>
    </table>
    <div class = 'infoBoxBreakBar'>Science Plots</div>
    <div class = 'infoBoxPlotDiv'>
        <img class = 'infoBoxPlotImage'
            src = '/static/images/infoBox2DPlot.png'
            onclick="deployPlots('%s')">
        </img>
    </div>
    <div class = 'infoBoxBreakBar'>Model Comparisons</div>
    <div class = 'infoBoxPlotDiv'>
        <img class = 'infoBoxPlotImage'
            src = "%s"
            onclick="modComps('%s')">
        </img>
    </div>
    """ % (public_name, infobox_image, last_surfaced,
           operator, vehicle_model, project, last_lon, last_lat,
           data_source, vehicle, mod_comp_path, mod_comp_path)
    return(last_pos)


def gandalf_gdac_sensors_csv(vehicle):
    """
    Name:       gdac_gdac_sensors_csv
    Author:     robertdcurrier@gmail.com
    Created:    2022-06-13
    Modified:   2022-06-13
    Notes:      creates sensors.csv from dataframe. This is the gdac equivalent
                of dba_merge into sensors.csv. We then use sensors.csv for
                plots and kml generation.
    """
    logging.warning("gandalf_gdac_sensors_csv(%s)" % vehicle)
    config = get_vehicle_config(vehicle)
    df = gdac_to_df(vehicle)
    if (len(df)) == 0:
        logging.warning('gandalf_gdac_sensors_csv(%s): 0 length DF', vehicle)
        return False

    csv_file = config['gandalf']['deployed_sensors_csv']
    logging.info("gandalf_gdac_sensors_csv(): Writing to %s" % csv_file)
    try:
        df.to_csv(csv_file, na_rep='NaN',index=False)
    except Exception:
        logging.warning('gandalf_gdac_sensors_csv(): Failed to build CSV')
        pass


def gandalf_process_gdac(vehicle):
    """
    Name:       gdac_process_gdac
    Author:     robertdcurrier@gmail.com
    Created:    2022-06-13
    Modified:   2022-06-15
    Notes:      Entry point.  2022-06-15 added 'nogdac' arg so we can test
                without pulling JSON each time. Requires existing file.
    """
    logging.warning('gandalf_process_gdac(%s)' % vehicle)
    get_gdac_json(vehicle)
    results = gandalf_gdac_sensors_csv(vehicle)
    if results != False:
        track = gandalf_gdac_track(vehicle)
        return track
    else:
        logging.warning('gandalf_process_gdac(%s): Invalid DF', vehicle)
        return []

def get_cli_args():
    """What it say.

    Name:       get_cli_args
    Author:     robertdcurrier@gmail.com
    Created:    2018-11-06
    Modified:   2021-05-16
    """
    logging.debug('get_cli_args()')
    arg_p = argparse.ArgumentParser()
    arg_p.add_argument("-v", "--vehicle", help="vehicle name",
                       nargs="?", required='True')
    arg_p.add_argument("-n", "--nogdac", help="Don't pull from GDAC",
                       action="store_true")
    args = vars(arg_p.parse_args())
    return args


if __name__ == "__main__":
    logging.basicConfig(level=logging.info)
    args = get_cli_args()
    vehicle = args['vehicle']
    gandalf_process_gdac(vehicle)
