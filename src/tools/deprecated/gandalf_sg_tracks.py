#!/usr/bin/env python3
"""
Creates surface tracks in 'OG' style using csv and pandas

Name:       gandalf_sg_tracks.py
Author:     bob.currier@gcoos.org
Created:    2022-06-06
Modified:   2022-06-21
"""
import sys
import time
import gc
import json
import time
import logging
import math
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import cmocean
import datetime
from matplotlib import dates as mpd
from matplotlib import pyplot as plt
from matplotlib import colors as colors
from matplotlib import cm as cm
from gandalf_utils import get_vehicle_config, get_sensor_config, flight_status
from gandalf_slocum_local import dinkum_convert
from geojson import Feature, Point, FeatureCollection, LineString


def slim_df(vehicle, data_frame):
    """
    Name:       slim_df
    Author:     bob.currier@gcoos.org
    Created:    2022-05-19
    Modified:   2022-06-06
    Notes:      Drops excessive lat/lons
    """
    logging.info('slim_df(%s)' % vehicle)
    config = get_vehicle_config(vehicle)

    data_frame.latitude = data_frame.latitude.round(6)
    data_frame.longitude = data_frame.longitude.round(6)
    slim_df = data_frame.drop_duplicates(['latitude'])
    slim_df = slim_df.drop_duplicates(['longitude'])
    slim_df = slim_df.drop_duplicates(['ctd_time'])
    slim_df = slim_df.drop_duplicates(['time'])

    logging.info('slim_df(%s): returning slim_df', vehicle)
    return slim_df


def write_geojson_file(data_source, data):
    """
    Name:       write_geojson_file
    Author:     robertdcurrier@gmail.com
    Modified:   2020-05-26
    Notes:      Writes out geojson file for Jquery AJAX loading
    """
    logging.info("write_geojson_file(%s)" % data_source)
    fname = '/data/gandalf/deployments/geojson/%s.json' % data_source
    outf = open(fname, 'w')
    print(data, file=outf)
    outf.flush()
    outf.close()


def gen_last_pos(vehicle, df):
    """
    Name:       gen_last_pos
    Author:     robertdcurrier@gmail.com
    Created:    2022-06-06
    Modified:   2022-06-15
    Notes:      Makes last pos html and icon
                2022-06-15: Added KeyError as USM SG not report eng_head
                2022-06-20: Added latitude and longitude to properties so we
                can use in new 'teleport' function on dashboard
    """
    logging.debug('gen_last_pos(): making last_pos')
    config = get_vehicle_config(vehicle)
    vehicle = config['gandalf']['vehicle']
    # Date math to calculate days_wet
    deploy_date = (time.strftime("%Y-%m-%d",
                                 time.strptime(config["trajectory_datetime"],
                                                "%Y%m%dT%H%M")))
    date_obj = datetime.datetime.strptime(deploy_date, "%Y-%m-%d").date()
    current_date = datetime.date.today()
    days_wet = (current_date - date_obj).days
    infobox_image = config["gandalf"]["infoBoxImage"]
    public_name = config['gandalf']['public_name']
    operator = config['gandalf']['operator']
    vehicle_model = config['gandalf']['vehicle_model']
    project = config['gandalf']['project']
    data_source = config["gandalf"]["data_source"]
    last_lon = df.iloc[-1]['longitude'].round(4)
    last_lat = df.iloc[-1]['latitude'].round(4)
    last_pos = Point((last_lon, last_lat))
    teleport_zoom = config["gandalf"]["teleport_zoom"]
    # Not all SG report eng_head
    try:
        bearing = df.iloc[-1]['eng_head']
    except KeyError:
        bearing = 0
    index = -1
    epoch = df.iloc[index]['ctd_time']
    # 2023-01-17 added this as we were seeing lots of trailing NaNs in time
    while np.isnan(epoch):
        logging.info("gen_last_pos(%s): %d, %0.2f", vehicle, index, epoch)
        epoch = df.iloc[index]['ctd_time']
        index -=1
    logging.info("gen_last_pos(%s): %d, %0.2f", vehicle, index, epoch)
    last_surfaced = (datetime.datetime.fromtimestamp(epoch).
                     strftime("%Y-%m-%d %H:%M UTC"))
    last_pos = Feature(geometry=last_pos, id='last_pos')
    last_pos.properties['vehicle'] = vehicle
    last_pos.properties['last_surfaced'] = last_surfaced
    last_pos.properties['bearing'] = bearing-90 # compensate for icon rotation
    last_pos.properties['latitude'] = last_lat
    last_pos.properties['longitude'] = last_lon
    last_pos.properties['teleport_zoom'] = teleport_zoom
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
        <td class='td_infoBoxSensor'>Bearing:</td>
        <td class='td_infoBoxData'>%s degrees</td>
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
    """ % (public_name, infobox_image, last_surfaced,
           operator, vehicle_model, project, last_lon, last_lat, bearing,
           data_source, vehicle)
    return(last_pos)


def gen_df(vehicle):
    """
    Name:       gen_df
    Author:     robertdcurrier@gmail.com
    Created:    2022-06-06
    Modified:   2022-06-16
    Notes:      Makes a pandas df from sensors.csv
    """
    logging.info('gen_df(%s)' % vehicle)
    status = flight_status(vehicle)
    config = get_vehicle_config(vehicle)

    if status == 'deployed':
        data_dir = config['gandalf']['deployed_data_dir']
        plot_dir = config['gandalf']['plots']['deployed_plot_dir']
    if status == 'recovered':
        data_dir = config['gandalf']['post_data_dir_root']
        plot_dir = config['gandalf']['plots']['postprocess_plot_dir']

    file_name = "%s/processed_data/sensors.csv" % (data_dir)
    data_frame = pd.read_csv(file_name)
    return(data_frame)


def gandalf_sg_track(vehicle):
    """
    Name:       gandalf_sg_track
    Author:     robertdcurrier@gmail.com
    Created:    2018-11-06
    Modified:   2022-10-11
    Notes:      main loop. Each vehicle's csv file is used, slim_df removes
                lat/lon dupes and gen_track makes a JSON fC track.
                2022-10-11: rdc cleaned up track generation code. Run time now
                neglible.
    """
    logging.info('gen_track(%s)' % vehicle)
    fcoll = []
    coords = []
    lats = []
    lons = []
    features = []

    config = get_vehicle_config(vehicle)
    public_name = config['gandalf']['public_name']
    operator = config['gandalf']['operator']
    vehicle_type = config['gandalf']['vehicle_type']
    project = config['gandalf']['project']

    df = gen_df(vehicle)
    slim = slim_df(vehicle, df)
    logging.info('gandalf_sg_track(%s): Iterating over slim_df', vehicle)

    idx = 0
    for lat in slim['latitude']:
        lon = (slim['longitude'].iloc[idx])
        idx+=1
        # Need this in the config file with better parms 2022-10-11
        if lat > 10 and lon < -60:
            coords.append((lon, lat))
    logging.info('gandalf_sg_track(%s): Finished iterating slim_df', vehicle)
    logging.info('gandalf_sg_track(%s): Making linestring', vehicle)

    track = LineString(coords)
    track = Feature(geometry=track, id='track')
    track.properties['style'] = (config['gandalf']['style'])

    last_pos = gen_last_pos(vehicle, df)
    features.append(last_pos)

    # 2022-10-12 hack to prevent USM SG from making whackadoo track
    if vehicle != 'sg677':
        features.append(track)

    return features


def get_cli_args():
    """What it say.

    Author: robertdcurrier@gmail.com
    Created:    2018-11-06
    Modified:   2021-05-16
    """
    logging.info('get_cli_args()')
    arg_p = argparse.ArgumentParser()
    arg_p.add_argument("-v", "--vehicle", help="vehicle name",
                       nargs="?", required='True')
    args = vars(arg_p.parse_args())
    return args


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start = time.time()
    # CLI version -- normally gen_tracks called from other code
    args = get_cli_args()
    vehicle = args['vehicle']
    features = gandalf_sg_track(vehicle)
    end = time.time()
    ttime = end - start
    logging.info('gandalf_sg_tracks(): Run time was %s' % ttime)
