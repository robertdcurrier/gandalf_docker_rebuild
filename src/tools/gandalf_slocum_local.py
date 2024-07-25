#!/usr/bin/env python3
"""
Name:       gandalf_harvest_local.py
Created:    2018-07-10
Modified:   2018-07-10
Author:     bob.currier@gcoos.org
Inputs:     Dinkum binary files, ascii log files
Outputs:    GeoJSON Feature Collections, plots
"""
from datetime import datetime
from datetime import date
from datetime import timedelta
import glob
import time
import re
import sys
import math
import datetime
import simplekml
import logging
import pandas as pd
from decimal import getcontext, Decimal
from geojson import LineString, FeatureCollection, Feature, Point
from gandalf_slocum_binaries_v2 import process_binaries
from gandalf_calc_sensors import calc_salinity
from gandalf_calc_sensors import calc_density
from gandalf_calc_sensors import calc_soundvel
from gandalf_utils import get_vehicle_config, flight_status
from gandalf_utils import dinkum_convert
from gandalf_utils_2 import get_modcomp_path, eez_early_warning
from gandalf_slocum_to_kml import parse_log_files, get_log_files, slocum_kmz


def make_slocum_surf_marker(row, config):
    """
    Name:       make_surf_marker
    Author:     robertdcurrier@gmail.com
    Created:    2019-01-04
    Modified:   2019-01-04
    Notes:      Makes marker with infobox html for each report
    """
    point = Point([float(row['longitude']), float(row['latitude'])])
    surf_marker = Feature(geometry=point, id='surf_marker')
    if(row['curr_time'] != 'NaN'):
        last_surfaced = (datetime.datetime.fromtimestamp(row['curr_time']).
                         strftime("%Y-%m-%d %H:%M UTC"))
    else:
        last_surfaced = 'NaN'

    infobox_image = config["gandalf"]["infoBoxImage"]
    surf_marker.properties['html'] = """
        <center><img src='%s'></img></center>
        <hr>
        <h5><center><span class='infoBoxHeading'>Status</span></center></h5>
        <table class='infoBoxTable'>
        <tr><td class='td_infoBoxSensor'>Vehicle:</td><td>%s</td></tr>
        <tr><td class='td_infoBoxSensor'>Date/Time:</td><td>%s</td></tr>
        <tr><td class='td_infoBoxSensor'>Because Why:</td><td>%s</td></tr>
        <tr><td class='td_infoBoxSensor'>Mission:</td><td>%s</td></tr>
        <tr><td class='td_infoBoxSensor'>Position:</td><td>%0.4fW/%0.4fN</td></tr>
        <tr><td class='td_infoBoxSensor'>WP Range:</td><td>%0.2f meters</td></tr>
        <tr><td class='td_infoBoxSensor'>WP Bearing:</td><td>%d degrees</td></tr>
        </table>
        """ % (infobox_image, config['gandalf']['public_name'], last_surfaced,
               row['because_why'], row['mission_name'], row['longitude'],
               row['latitude'], float(row['waypoint_range']),
               int(row['waypoint_bearing']))
    return surf_marker


def make_local_feature(data_frame, config):
    """
    Name:       make_local_feature()
    Author:     bob.currier@gcoos.org
    Created:    2018-07-01
    Modified:   2022-06-21
    Notes:      Changed this to match the new version from NavOcean work.
                We have separate features for track, lastPos and surface reports.
                This allows a clean way to handle all features in gandalf.js by
                using the id. We need to switch from one feature called 'feature'
                to 'track', 'last_pos' and 'surf_marker.'
                2022-06-21: Added latitude, longitude and teleport_zoom to
                features for use with new dashboard 'Teleport' function.
    """

    coords = []
    features = []

    vehicle = config['gandalf']['vehicle']
    deployment_date = config['trajectory_datetime']
    public_name = config['gandalf']['public_name']
    logging.info("last_pos(): Using %s for public_name" % public_name)
    operator = config['gandalf']['operator']
    vehicle_type = config['gandalf']['vehicle_type']
    project = config['gandalf']['project']
    data_source = config["gandalf"]["data_source"]

    # get modcomp path
    mod_comp_path = get_modcomp_path(config)


    # Drop duplicate coords
    data_frame = data_frame.drop_duplicates(subset=('longitude','latitude'))
    # Need to remove 0.0 lat/lons
    # 2019-01-11 added column names when creating DF so need
    # to switch from index access to using name

    logging.debug('make_local_feature(): testing for 0 lon/lats')
    for index, row in data_frame.iterrows():
        if row['longitude'] == 0.0 and row['latitude'] == 0.0:
            data_frame = data_frame.drop([index])

    logging.debug('make_local_feature(): making points...')
    for index, row in data_frame.iterrows():
        point = Point([float(row['longitude']), float(row['latitude'])])
        coords.append(point)
        if (row['curr_time']) != 'NaN':
            last_surfaced = (datetime.datetime.fromtimestamp(row['curr_time']).
                             strftime("%Y-%m-%d %H:%M UTC"))

    because_why = data_frame['because_why'].iloc[-1]
    mission_name = data_frame['mission_name'].iloc[-1]


    waypoint_lon = float(data_frame['waypoint_lon'].tail(1))
    waypoint_lat = float(data_frame['waypoint_lat'].tail(1))
    # 2023-08-30 Add config file setting'display_waypoints' and test
    # here. If false, skip waypoint generation. Might need to mod the
    # JS display code as well.

    waypoint_point = Point([waypoint_lon, waypoint_lat])
    waypoint_range = int(data_frame['waypoint_range'].tail(1))/1000
    waypoint_bearing = int(data_frame['waypoint_bearing'].tail(1))
    # Build the track and style it
    logging.debug('make_local_feature(): making track')
    track = LineString(coords)
    track = Feature(geometry=track, id='track')
    track.properties['style'] = (config['gandalf']['style'])
    features.append(track)
    """
    # Surface markers
    for index, row in data_frame.iterrows():
        marker = make_slocum_surf_marker(row, config)
        features.append(marker)
    """
    # Last Pos w/InfoBox HTML
    last_lon = float(coords[-1]['coordinates'][0])
    last_lat = float(coords[-1]['coordinates'][1])
    teleport_zoom = config['gandalf']['teleport_zoom']

    deployment_date = (time.strftime("%Y-%m-%d",
                                     time.strptime(config["trajectory_datetime"],
                                                   "%Y%m%dT%H%M")))
    logging.debug('make_local_feature(): making last_pos')
    last_pos = Point((last_lon, last_lat))
    last_pos = Feature(geometry=last_pos, id='last_pos')

    # 2023-09-20-2023 Implemeted EEZ warning
    eez = eez_early_warning(vehicle, [last_lat, last_lon])
    if eez:
        last_pos.properties['eez_early_warning'] = True
    else:
        last_pos.properties['eez_early_warning'] = False

    deployment_date = (time.strftime("%Y-%m-%d",
                       time.strptime(config["trajectory_datetime"],
                                     "%Y%m%dT%H%M")))


    # Date math to calculate days_wet
    date_obj = datetime.datetime.strptime(deployment_date, "%Y-%m-%d").date()
    current_date = datetime.date.today()
    days_wet = (current_date - date_obj).days
    infobox_image = config["gandalf"]["infoBoxImage"]
    data_source = config["gandalf"]["data_source"]
    last_pos.properties['vehicle'] = (config['gandalf']['vehicle'])
    last_pos.properties['public_name'] = public_name
    last_pos.properties['data_source'] = data_source
    last_pos.properties['style'] = (config['gandalf']['style'])
    last_pos.properties['currPosIcon'] = (config['gandalf']['currPosIcon'])
    last_pos.properties['wpIcon'] = (config['gandalf']['wpIcon'])
    last_pos.properties['iconSize'] = (config['gandalf']['iconSize'])
    last_pos.properties['deployment_date'] = deployment_date
    last_pos.properties['last_surfaced'] = last_surfaced
    last_pos.properties['days_wet'] = days_wet
    last_pos.properties['plot_url'] = config['gandalf']['plots']['deployed_plot_dir']
    last_pos.properties['kmz_url'] = (config['gandalf']['kmz_url'])
    last_pos.properties['latitude'] = last_lat
    last_pos.properties['longitude'] = last_lon
    last_pos.properties['teleport_zoom'] = teleport_zoom
    last_pos.properties['waypoint_point'] = waypoint_point
    last_pos.properties['waypoint_range'] = waypoint_range
    last_pos.properties['waypoint_bearing'] = waypoint_bearing
    last_pos.properties['waypoint_html'] = """
	<table class='infoBoxTable'>
        <h5><center><span class='infoBoxHeading'>%s waypoint</span></center></h5>
        <tr><td class='td_infoBoxSensor'>Position:</td><td>%0.4fW/%0.4fN</td></tr>
        </table>
    """ % (last_pos.properties['public_name'], waypoint_lon, waypoint_lat)
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
        <td class='td_infoBoxSensor'>Because Why:</td>
        <td class='td_infoBoxData'>%s</td>
    </tr>
    <tr>
        <td class='td_infoBoxSensor'>Mission:</td>
        <td class='td_infoBoxData'>%s</td>
    </tr>
    <tr>
        <td class='td_infoBoxSensor'>Last Position:</td>
        <td class='td_infoBoxData'>%sW %sN</td>
    </tr>
    <tr>
        <td class='td_infoBoxSensor'>Waypoint:</td>
        <td class='td_infoBoxData'>%skm at %s degrees</td>
    </tr>

    <tr>
        <td class='td_infoBoxSensor'>Data Source:</td>
        <td class='td_infoBoxData'><a href="https://gliders.ioos.us/map">%s</a>
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
            src = '%s'
            onclick="modComps('%s')">
        </img>
    </div>

    """ % (public_name, infobox_image, last_surfaced, because_why, mission_name,
           last_lon, last_lat, waypoint_range, waypoint_bearing, data_source,
           vehicle,mod_comp_path,mod_comp_path)
    features.append(last_pos)
    fC = FeatureCollection(features)
    return fC


def get_slocum_surfreps(vehicle_list):
    """
    Here we initiate retrieval of LOCAL data and conversion into a
    GANDALF-compliant feature collection.
    """
    # We iterate over all vehicles in list.
    # Do surfacings and create GeoJSON FC of all deployed local vehicles
    features = []
    for vehicle in vehicle_list:
        logging.info("get_slocum_surfreps(%s)" % vehicle)
        config = get_vehicle_config(vehicle)
        log_files = get_log_files(config)
        if len(log_files) == 0:
            logging.info('No log files found.')
            return
        logging.info("%d log files found." % len(log_files))
        df = parse_log_files(config, log_files)
        # Add styling, icons, innerHTML, etc
        features.append(make_local_feature(df, config))
    # Do NOT make FeatureCollection here as we now combine into one file
    return features


def slocum_process_local(vehicle_list):
    """
    Processes binaries, calculates salinity and
    density, makes plots and kmz files. Surface
    reports and geoJSON generation are done in
    get_slocum_surfreps
    """
    skip_list = ['ng655', 'ng427']
    for vehicle in vehicle_list:
        logging.info("slocum_process_local(%s)" % vehicle)
        config = get_vehicle_config(vehicle)
        mod_comp_path = get_modcomp_path(config)
        #
        if vehicle not in skip_list:
            process_binaries(config, vehicle)
            calc_salinity(config, vehicle)
            calc_density(config, vehicle)
            calc_soundvel(config, vehicle)
            slocum_kmz(vehicle)

def write_local_geojson(vehicle, data):
    """
    DOCSTRING
    """
    logging.info("write_local_geojson(%s)" % vehicle)
    fname = ("%s.json" % (vehicle))
    logging.info("write_local_geojson(): Writing %s" % fname)
    outf = open(fname,'w')
    logging.info(data, file=outf)
    outf.flush()
    outf.close()

if __name__ == '__main__':
    """
    For command line use
    """

    logging.basicConfig(level=logging.WARNING)
    if len(sys.argv) != 2:
        logging.warning("Usage: gandalf_slocum_local vehicle")
        sys.exit()
    else:
        vehicle = sys.argv[1]
        slocum_process_local([vehicle])
        get_slocum_surfreps([vehicle])
