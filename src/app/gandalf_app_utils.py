#!/usr/bin/env python3
import os
import json
import sys
import datetime
import logging
from datetime import timezone
"""
Name: gandalf_utils
Author: robertdcurrier@gmail.com
Created: 2018-05-10
Modified: 2020-06-25
Notes: Dashboard json, get deployed vehicles, etc
Big redo on modified date. This was written before config files got so large
and included GDAC info. I stopped using the raw vehicle_config and just
extract what's needed and put into a dict called vjson. This eliminates a lot
of the extraneous crap.
"""

def get_vehicle_config(vehicle):
    """
    Sorta evident...
    """
    logging.debug("get_vehicle_config(%s)" % vehicle)
    # get config debug for each vehicle
    data_file = ("/data/gandalf/gandalf_configs/vehicles/%s/ngdac/deployment.json"
                 % vehicle)
    config = open(data_file,'r').read();
    config = json.loads(config)
    return config


def get_summaries():
    """
    Gets archived deployment data
    """
    data_file = ("/data/gandalf/gandalf_configs/deployment_summaries/summaries.json")
    config = open(data_file,'r').read();
    summaries = json.loads(config)
    return summaries


def get_portal_map_dash(vehicle, date):
    """
    Loads summaries.json and extracts single record
    for use in map portal dashboard
    """
    # don't reinvent the wheel
    summaries = get_summaries()
    # Lower case everybody as some vehicles are mixed case
    for record in summaries:
        if vehicle in record['vehicle'].lower():
            if date in record['deployed']:
                return record


def get_waveglider_dash():
    """
    Name:           get_dashboard_json
    Author:         bob.currier@gcoos.org
    Date:           2023-01-06
    Modified:       2023-01-06
    Notes:          Waveglider geojson is very different than other vehicles so we need
                    to have a specialized parser. We extract the pertinent info, convert
                    to standard gandalf dashboard json format and return the json data.
    """
    data_path = '/data/gandalf/deployments/geojson'
    config_file = '%s/waveglider.json' % (data_path)
    the_config = (open(config_file).read())
    if len(the_config) != 0:
        the_config = json.loads(the_config)
    print('doing waveglider json stuff, yo.')
    return


def get_dashboard_json():
    """
    Name:           get_dashboard_json
    Author:         bob.currier@gcoos.org
    Date:           2019-01-10
    Modified:       2022-06-07
    Notes:          We need to iterate over all three vehicle type files:
                    slocal, erddap and seaglider. We pull vehicle info from
                    these files and then build JSON document w/format matching
                    what deployment.html template wants. Each vehicle gets
                    appended to dashboard_json[]. We return dashboard_json
                    and deployment.html can interate over using Jinja
                    '{% for vehicle in vehicles %}'

    """
    dashboard_json = []
    #vehicle_types = ['local', 'erddap', 'seagliders','gdac']
    vehicle_types = ['seagliders', 'local', 'gdac', 'erddap']
    data_path = '/data/gandalf/deployments/geojson'

    # Loop over all vehicle types (local, erddap, navocean)
    for v_type in vehicle_types:
        # For each type grab config file and convert to json
        config_file = '%s/%s.json' % (data_path, v_type)
        the_config = (open(config_file).read())
        if len(the_config) != 0:
            the_config = json.loads(the_config)

        # Go through each vehicle type config file and pull out vehicles
        for vehicle in the_config:
            for feature in vehicle['features']:
                # We only care about last_pos
                if feature['id'] == 'last_pos':
                    latitude = (feature['properties']['latitude'])
                    longitude = (feature['properties']['longitude'])
                    last_surfaced = (feature['properties']['last_surfaced'])
                    # Do the date math to set class for Dashboard last_surfaced
                    date_obj = datetime.datetime.strptime(last_surfaced,
                                              "%Y-%m-%d %H:%M UTC")
                    current_date = datetime.datetime.now()
                    last_call = (current_date - date_obj).days

                    days_wet = (feature['properties']['days_wet'])
                    vehicle = (feature['properties']['vehicle'])
                    vehicle_config = get_vehicle_config(vehicle)

                    # create the dict
                    vjson = {}
                    # add calculated data
                    vjson['last_surfaced'] = last_surfaced
                    vjson['latitude'] = latitude
                    vjson['longitude'] = longitude
                    vjson['last_call'] = last_call
                    vjson['days_wet'] = days_wet
                    # get the rest from the config file
                    vjson['deployment_date'] = (vehicle_config['gandalf']
                                                ['deployment_date'])
                    vjson['data_source'] = (vehicle_config['gandalf']
                                            ['data_source'])
                    vjson['dash_status'] = (vehicle_config['gandalf']
                                            ['dash_status'])
                    vjson['PI'] = vehicle_config['gandalf']['PI']
                    vjson['public_name'] = (vehicle_config['gandalf']
                                            ['public_name'])
                    vjson['vehicle_type'] = (vehicle_config['gandalf']
                                             ['vehicle_type'])
                    vjson['operator'] = vehicle_config['gandalf']['operator']
                    vjson['project'] = vehicle_config['gandalf']['project']
                    vjson['kmz_url'] = vehicle_config['gandalf']['kmz_url']
                    vjson['vehicle'] = vehicle_config['gandalf']['vehicle']
                    logging.info('get_dashboard_json(%s)', vehicle)
                    dashboard_json.append(vjson)
    # Sort by name in ascending order
    dashboard_json = sorted(dashboard_json, key=lambda i: i['public_name'])
    return dashboard_json


if __name__ == '__main__':
    """
    For command line testing
    """
    logging.basicConfig(level=logging.INFO)
    logging.info('gandalf_app_utils')
    dash_json = get_dashboard_json()
    #wg_dash_json = get_waveglider_dash()
    print(sorted(dash_json, key=lambda i: i['public_name']))
