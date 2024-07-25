#!/usr/bin/env python3
"""
Name:       gandalf_navocean_posrep
Author:     bob.currier@gcoos.org
Created:    2016-06-10
Modified:   2018-12-12
Inputs:     Navocean ASV data in JSON format from PostGIS table
Outputs:    feature collections in database
pylint:     Your code has been rated at 9.59/10
"""
import sys
import os
import time
import datetime
import json
import requests
import pandas as pd
from geojson import Feature, Point, FeatureCollection, LineString
from gandalf_utils import get_vehicle_config, get_sensor_config
# Chlorophyll color map
from chloroMap import chloroMap
#


def cmap_chloro(value, min, max):
    """
    """
    index = int((254/max) * value)
    hexString = chloroMap[index];
    return hexString


def get_navocean_science_sensors(vehicle):
    """
    Name:       get_navocean_science_sensors
    Author:     robertdcurrier@gmail.com
    Created:    2019-01-07
    Modified:   2019-01-07
    Notes:      Gets list of science sensors from config file
    """
    print("get_navocean_science_sensors(%s)" % vehicle)
    config = get_vehicle_config(vehicle)
    science_sensors = config['gandalf']['science_sensor_list']
    return science_sensors


def make_navocean_df(vehicle):
    """
    Name:       make_vela_fc_pandas
    Author:     robertdcurrier@gmail.com
    Created:    2019-01-03
    Modified:   2019-01-03
    """
    print("make_navocean_df()...")
    config = get_vehicle_config(vehicle)
    # Turn json_data into pandas df
    data_frame = pd.read_json(config['gandalf']['vela_url'])
    return data_frame


def make_navocean_track(data_frame, vehicle):
    """
    Name:       make_track
    Author:     robertdcurrier@gmail.com
    Created:    2019-01-03
    Modified:   2019-01-03
    Notes:      track only
    """
    print("make_navocean_track(%s)..." % vehicle)
    # Turn json_data into pandas df
    coords = []
    for index, row in data_frame.iterrows():
        coords.append([float(row['gps']['lon']), float(row['gps']['lat'])])
    track = LineString(coords)
    return track


def make_surf_marker(row, config, chloro_max, chloro_min):
    """
    Name:       make_surf_marker
    Author:     robertdcurrier@gmail.com
    Created:    2019-01-04
    Modified:   2019-02-06
    Notes:      Makes marker with infobox html for each report
                We added chloro_max and chloro_min so we could
                do dynamic color mapping for each surface marker.
    """
    point = Point((float(row['gps']['lon']),
                  float(row['gps']['lat'])))
    surf_marker = Feature(geometry=point, id='surf_marker')
    # surf_marker.properties['chloro_max'] = chloro_max
    # surf_marker.properties['chloro_min'] = chloro_min
    # surf_marker.properties['chlorophyll'] = float(row['science']['chlorophyll'])
    surf_marker.properties['html'] = """
	<h5><center><span class='infoBoxHeading'>Status</span></center></h5>
        <table class='infoBoxTable'>
        <tr><td class='td_infoBoxSensor'>Organization:</td><td>Navocean</td></tr>
        <tr><td class='td_infoBoxSensor'>Vehicle:</td><td>VELA</td></tr>
        <tr><td class='td_infoBoxSensor'>Date/Time:</td><td>%s</td></tr>
        <tr><td class='td_infoBoxSensor'>Position:</td><td>%0.4fW/%0.4fN</td></tr>
        <tr><td class='td_infoBoxSensor'>Heading:</td><td>%0.2f</td></tr>
        <tr><td class='td_infoBoxSensor'>Speed:</td><td>%0.2f knots</td></tr>
        </table>
        <hr>
        <h5><center><span class='infoBoxHeading'>Science</span></center></h5>
        <table class='infoBoxTable'>
    """ % (row['dt'], float(row['gps']['lon']), float(row['gps']['lat']),
           float(row['phr']['heading']),float(row['gps']['speed']))
    science_html = ""
    # We used to iterate over science_sensors but need to refer directly for now
    # Chlorophyll
    chloro = float(row['science']['chlorophyll'])
    chloro_color = cmap_chloro(chloro, chloro_min, chloro_max)
    surf_marker.properties['chloro_color'] = chloro_color

    html_row = "<tr><td class='td_infoBoxSensor'>Chlorophyll:</td><td>%0.2f ug/L</td></tr>" % (chloro)
    science_html = science_html + html_row
    phycocyanin = float(row['science']['phycocyanin'])
    html_row = "<tr><td class='td_infoBoxSensor'>Phycocyanin:</td><td>%0.2f ug/L</td></tr>" % (phycocyanin)
    science_html = science_html + html_row
    cdom = float(row['science']['CDOM'])
    html_row = "<tr><td class='td_infoBoxSensor'>CDOM:</td><td>%0.2f PPB</td></tr>" % (cdom)
    science_html = science_html + html_row
    surf_marker.properties['html'] = surf_marker.properties['html'] + science_html + "</table>"
    return surf_marker


def scale_science(data_frame):
    """
    Scale fluor output from TI according to Beckler
    Will need to adjust based on calibration of instrument
    """
    for index, row in data_frame.iterrows():
        # scale chlorophyll per JB
        chloro = float(row['science']['chlorophyll'])
        chloro = chloro/400
        row['science']['chlorophyll'] = chloro

        # scale CDOM per JB
        cdom = float((row['science']['CDOM']))
        cdom = cdom*.001
        row['science']['CDOM'] = cdom

        # scale Phycocyanin per JB
        phycocyanin = float(row['science']['phycocyanin'])
        phycocyanin = phycocyanin/400
        row['science']['phycocyanin'] = phycocyanin
    # return scaled data_frame
    return data_frame

def make_navocean_features(data_frame, vehicle):
    """
    Name:       make_track
    Author:     robertdcurrier@gmail.com
    Created:    2019-01-03
    Modified:   2019-01-03
    Notes:      Makes feature of all reporting locations w/infobox
                One feature per vehicle...
    """
    features = []
    print("make_navocean_features(%s)..." % vehicle)
    config = get_vehicle_config(vehicle)
    science_sensors = get_navocean_science_sensors(vehicle)
    track = make_navocean_track(data_frame, vehicle)

    # first row has current into
    row = data_frame.iloc[0]

    # heading and speed
    heading = float(row['phr']['heading'])
    speed = float(row['gps']['speed'])
    the_lon = float(row['gps']['lon'])
    the_lat = float(row['gps']['lat'])

    # convert Navocean date format to Gandalf date format
    last_surfaced = datetime.datetime.strptime(row['dt'], "%Y-%m-%d %H:%M:%S")
    last_surfaced = datetime.datetime.strftime(last_surfaced, "%Y-%m-%d %H:%M UTC")

    # Track
    track_name = "%s_track" % vehicle
    track = Feature(geometry=track, id='track')
    track.properties['style'] = (config['gandalf']['style'])
    features.append(track)


    # scale science sensors before we iterate
    data_frame = scale_science(data_frame)

    # Get min/max for chloro -- very non pythonic but it works
    chloro_min = 0
    chloro_max = 0
    for index, row in data_frame.iterrows():
        chloro = row['science']['chlorophyll']
        if chloro > chloro_max:
            chloro_max = chloro
        if chloro < chloro_min:
            chloro_min = chloro

    # Surface markers using scaled science and chloro max/min
    print("make_surf_markers()")
    for index, row in data_frame.iterrows():
        """
        2019-02-05
        Here we scale the science sensors as the values coming from
        the instrument aren't directly useful. We'll need to refine
        these formula based on input from Turner Instruments but for
        now they get us close enough.

        Color mapping now done directly in Python. We do here via
        chloro_map (will modify for all sensors soon) and then add
        chloro_color as a feature rather than having to do the work
        in the browser. The JS code then simply refers to
        feature.properties.chloro_color for each maker/feature. Voila --
        no work in the browser as the color is pre-picked. W00t!

        """

        marker = make_surf_marker(row, config, chloro_max, chloro_min)
        features.append(marker)

    # Las Pos and InfoBox w/html
    last_pos = Point((the_lon, the_lat))
    last_pos = Feature(geometry=last_pos, id='last_pos')

    deployment_date = (time.strftime("%Y-%m-%d",
                       time.strptime(config["trajectory_datetime"],
                                     "%Y%m%dT%H%M")))

    # Date math to calculate days_wet
    date_obj = datetime.datetime.strptime(deployment_date, "%Y-%m-%d").date()
    current_date = datetime.date.today()
    days_wet = (current_date - date_obj).days
    data_source = config["gandalf"]["data_source"]
    # We don't worry about chloro_max/chloro_min for last_pos
    # as sailboat icon covers surf marker
    last_pos.properties['vehicle'] = (config['gandalf']['vehicle'])
    last_pos.properties['data_source'] = data_source
    last_pos.properties['style'] = (config['gandalf']['style'])
    last_pos.properties['currPosIcon'] = (config['gandalf']['currPosIcon'])
    last_pos.properties['iconSize'] = (config['gandalf']['iconSize'])
    last_pos.properties['deployment_date'] = deployment_date
    last_pos.properties['last_surfaced'] = last_surfaced
    last_pos.properties['days_wet'] = days_wet
    last_pos.properties['plot_url'] = config['gandalf']['plots']['deployed_plot_dir']
    last_pos.properties['kmz_url'] = (config['gandalf']['kmz_url'])
    last_pos.properties['html'] = """
        <center><img src='/static/images/vela_infobox_img.png'></img></center>
        <h5><center><span class='infoBoxHeading'>Status</span></center></h5>
        <table class='infoBoxTable'>
        <tr><td class='td_infoBoxSensor'>Vehicle:</td><td>VELA</td></tr>
        <tr><td class='td_infoBoxSensor'>Organization:</td><td>Navocean</td></tr>
        <tr><td class='td_infoBoxSensor'>Date/Time:</td><td>%s</td></tr>
        <tr><td class='td_infoBoxSensor'>Position:</td><td>%0.4fW/%0.4fN</td></tr>
        <tr><td class='td_infoBoxSensor'>Heading:</td><td>%0.2f</td></tr>
        <tr><td class='td_infoBoxSensor'>Speed:</td><td>%0.2f knots</td></tr>
        </table>
        """ % (last_surfaced, the_lon, the_lat, heading, speed)

    science_html = """
        <h5><center><span class='infoBoxHeading'>Science</span></center></h5>
        <table class='infoBoxTable'>"""
    # We used to iterate over science_sensors but need to refer directly for now
    chloro = float(row['science']['chlorophyll'])
    html_row = "<tr><td class='td_infoBoxSensor'>Chlorophyll:</td><td>%0.2f ug/L</td></tr>" % (chloro)
    science_html = science_html + html_row
    phycocyanin = float(row['science']['phycocyanin'])
    html_row = "<tr><td class='td_infoBoxSensor'>Phycocyanin:</td><td>%0.2f ug/L</td></tr>" % (phycocyanin)
    science_html = science_html + html_row
    cdom = float(row['science']['CDOM'])
    html_row = "<tr><td class='td_infoBoxSensor'>CDOM:</td><td>%0.2f PPB</td></tr>" % (cdom)
    science_html = science_html + html_row

    last_pos.properties['html'] = last_pos.properties['html'] + science_html + "</table>"
    features.append(last_pos)
    fC = FeatureCollection(features)
    return fC


def process_navocean(navocean_sailboats):
    """
    Main method. Gets data stream, makes a pandas df,
    builds features of track, reports and last pos,
    appends features to list and returns list. List
    will be added to overall Gandalf features and made
    into feature collection
    """
    features = []
    print("process_navocean(%s)" % navocean_sailboats)
    for vehicle in navocean_sailboats:
        data_frame = make_navocean_df(vehicle)
        features.append(make_navocean_features(data_frame, vehicle))
    return features

if __name__ == "__main__":
    fC = process_navocean(['vela'])
    print(fC)
