#!/usr/bin/env python3
"""
Name:       gandalf_harvest_gdac.py
Created:    2018-06-07
Modified:   2022-06-09
Author:     bob.currier@gcoos.org
Notes:      Harvests non-GANDALF gliders from GDCAC ERRDAP server. Gliders
are returned as GeoJSON object that we can just drop on map.
NOTE: GDAC now reaturns FeatureCollection so we had to change iteration to
for feature in json_data['features']
Changed logging.info() to logging.info/warn

Update:     Changed get_vehicle_config as we modified config file structure
"""
import sys
import json
import datetime
import time
import requests
import itertools
import logging
from geojson import LineString, FeatureCollection, Feature, Point
from gandalf_utils import get_vehicle_config


def make_erddap_feature(json_data, config):
    """
    Make GeoJSON feature collection
    """
    vehicle = config['gandalf']['vehicle']
    public_name = config['gandalf']['public_name']
    logging.info("make_erddap_feature(%s)" % vehicle)
    operator = config['gandalf']['operator']
    vehicle_type = config['gandalf']['vehicle_type']
    project = config['gandalf']['project']
    data_source = config["gandalf"]["data_source"]

    features = []
    coords = []
    for feature in json_data['features']:
        coords.append(feature['geometry']['coordinates'])
        last_surfaced = feature['properties']['time']
        last_surfaced = (datetime.datetime.strptime(last_surfaced,
                         "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M UTC"))
    # Remove dupes from coords to save space/time/baby seals
    no_dupes = list(coords for coords, _ in itertools.groupby(coords))
    track = LineString(no_dupes)
    track = Feature(geometry=track, id='track')
    track.properties['style'] = (config['gandalf']['style'])
    features.append(track)

    last_lon = "%0.4f" % coords[len(coords)-1][0]
    last_lat = "%0.4f" % coords[len(coords)-1][1]

    # Last Pos w/InfoBox HTML
    the_lon = float(coords[-1][0])
    the_lat = float(coords[-1][1])
    logging.debug('make_local_feature(): making last_pos')
    last_pos = Point((the_lon, the_lat))
    feature = Feature(geometry=last_pos, id='last_pos')
    features.append(feature)

    deployment_date = (time.strftime("%Y-%m-%d",
                                     time.strptime(config
                                                   ["trajectory_datetime"],
                                                   "%Y%m%dT%H%M")))
    date_obj = datetime.datetime.strptime(deployment_date, "%Y-%m-%d").date()
    current_date = datetime.date.today()
    days_wet = (current_date - date_obj).days
    infobox_image = config["gandalf"]["infoBoxImage"]
    feature.properties['vehicle'] = vehicle
    feature.properties['public_name'] = public_name
    feature.properties['data_source'] = data_source
    feature.properties['style'] = (config['gandalf']['style'])
    feature.properties['currPosIcon'] = (config['gandalf']['currPosIcon'])
    feature.properties['iconSize'] = (config['gandalf']['iconSize'])
    feature.properties['deployment_date'] = deployment_date
    feature.properties['last_surfaced'] = last_surfaced
    feature.properties['days_wet'] = days_wet
    feature.properties['kmz_url'] = (config['gandalf']['kmz_url'])
    feature.properties['html'] = """
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
    """ % (public_name, infobox_image, last_surfaced,
           operator, vehicle_type, project, last_lon, last_lat, data_source,
           vehicle)
    fC = FeatureCollection(features)
    return fC


def get_gdac_json(vehicle_list):
    """
    Here we initiate retrieval of ERDDAP data and conversion into a
    GANDALF-compliant feature collection.
    Modified: 2020-10-21
    Notes:  We were fetching ERDDAP 3 times (track, plots, 3D) so we
    moved to one pull and write as text file for all further access
    """
    logging.info('get_gdac_json(): %s' % vehicle_list)
    features = []
    # We iterate over all vehicles in list.
    for vehicle in vehicle_list:
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
        with open(fname) as json_file:
            json_data = json.load(json_file)
        # Add styling, icons, innerHTML, etc
        feature = make_erddap_feature(json_data, config)
        # Do NOT make FeatureCollection here as we now combine into one file
        features.append(feature)
        logging.info("get_gdac_json(%s): returning features" % vehicle)
    return features

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # hardwired for testing
    vehicle_list=[sys.argv[1]]
    features = get_gdac_json(vehicle_list)
