#!/usr/bin/env python3
"""
Name:       gandalf_to_saildrone
Author:     robertdcurrier@gmail.com
Created:    2022-08-09
Modified:   2022-08-11

Notes:      Uses the Saildrone API to post updates to the SD Mission portal.
We first get a list of all deployed GANDALF vehicles and then extract the
lastest positions from the sensors.csv files and build a dict.  We iterate
over the dict and hit the SD API to update the last pos for each vehicle.

TO DO: Use pycurl vs hardwiring command and sending to os.system().
2022-08-11: Added -t and -d args. -t generates new token, -d runs in
debug mode printing command but not calling API.  ARGO floats now working.
"""
import os
import sys
import json
import requests
import logging
import time
import argparse
from calendar import timegm


def get_cli_args():
    """What it say.

    Author: robertdcurrier@gmail.com
    Created:    2018-11-06
    Modified:   2022-08-10
    """
    logging.debug('get_cli_args()')
    arg_p = argparse.ArgumentParser()
    arg_p.add_argument("-d", "--debug", help="Run but don't call API",
                       action="store_true")
    arg_p.add_argument("-t", "--token", help="Generate auth token",
                       action="store_true")
    args = vars(arg_p.parse_args())
    return args


def generate_auth_token():
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-08-09
    Modified:   2022-08-09
    Notes:      Hits the SD API and creates and auth token to be used in
                updating tracked assets
    """
    logging.warning("generate_auth_token(): YOU'RE GONNA BREAK SOME SHIT...")
    # Comment out the sys.exit() if we need a new token
    sys.exit()
    auth_token = "NONE"
    command = """
    curl --http1.1 -X POST https://developer-mission.saildrone.com/v1/auth --header 'Content-Type: application/json'  -d '{
"key": "e4qeRuZquTRVgnrR",
"secret": "Qrj93Z7jkXutdF6YpeQGHxbFMx9J6sV6"
}'"""
    auth_token = os.system(command)
    logging.info('generate_auth_token(): Got token %s', auth_token)
    return auth_token


def update_sdmp(pos_list):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-08-09
    Modified:   2022-08-10
    Notes:      Hits the SD API and does a PUT to update each vehicles
                position on the SD Mission Portal.
    """
    args = get_cli_args()

    for vehicle in pos_list:
        vehicle["token"] = "%s" % "%s"

    for vehicle in pos_list:
        data = json.dumps(vehicle)
        if isinstance(vehicle['mmsi'] , str):
            vehicle['mmsi'] = vehicle['mmsi'].lower()
        logging.debug('update_sdmp(): Updating %s', vehicle['mmsi'])
        command = """curl --http1.1 -X POST https://developer-mission.saildrone.com/v1/ais --header 'Content-Type: application/json'  --header 'authorization: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbiI6ImM5ZTVmMTFlLWRiM2EtNDg2Mi05YWMzLTFlYzI3MDI3MWM4MiIsImtleSI6ImU0cWVSdVpxdVRSVmduclIiLCJpYXQiOjE2NjAxNTk3NDIsImV4cCI6MTY2NzkzNTc0Mn0.SFEBH59e9Hjgm1_7qEIbJSzL_9CpB4GrEMUVyfzKvQg' -d '{
"mmsi": "%s",
"longitude": %s,
"latitude": %s,
"timestamp": %s,
"token" : "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbiI6ImM5ZTVmMTFlLWRiM2EtNDg2Mi05YWMzLTFlYzI3MDI3MWM4MiIsImtleSI6ImU0cWVSdVpxdVRSVmduclIiLCJpYXQiOjE2NjAxNTk3NDIsImV4cCI6MTY2NzkzNTc0Mn0.SFEBH59e9Hjgm1_7qEIbJSzL_9CpB4GrEMUVyfzKvQg"
}'""" % (vehicle['mmsi'], vehicle['longitude'], vehicle['latitude'],
         vehicle['timestamp'])

        if args['debug']:
            logging.info('update_sdmp(DEBUG): %s' % command)
        else:
            print('updating %s\n' % vehicle['mmsi'])
            os.system(command)
            print('\n')


def get_last_positions(vehicle_data):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-08-09
    Modified:   2022-08-09
    Notes:      reads geojson and get last pos of all vehicles in data file.
                This gets called once per vehicle type (slocum, erddap and
                seaglider so we return a list of dicts.)
    """
    last_positions = []
    for collection in vehicle_data:
        for feature in collection['features']:
            if feature['id'] == 'last_pos':
                public_name = feature['properties']['public_name']
                latitude = float(feature['geometry']['coordinates'][1])
                longitude = float(feature['geometry']['coordinates'][0])
                last_surfaced = feature['properties']['last_surfaced']
                utc_time = time.strptime(last_surfaced, "%Y-%m-%d %H:%M UTC")
                epoch_time = timegm(utc_time)
                position = {"mmsi" :  public_name, "longitude" : longitude,
                            "latitude" : latitude,
                            "timestamp" : epoch_time
                            }
                last_positions.append(position)
    return last_positions


def get_argo_positions():
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-08-10
    Modified:   2022-08-11
    Notes:      reads geojson and get last pos of all ARGO floats. We use
    run time epoch as timestamp given that there is no easy way to get epoch
    from argo.json, and since the floats only report every 10 days there's no
    need to be precise.
    """
    argo_positions = []
    epoch = int(time.time())
    logging.info('get_argo_positions()')
    data_file = '/data/gandalf/deployments/geojson/argo.json'
    try:
        with open(data_file) as json_data:
            jdata = json.loads(json_data.read())
    except ValueError as error:
        logging.warning(error)
    for collection in jdata:
        for feature in collection['features']:
            latitude = float(feature['geometry']['coordinates'][1])
            longitude = float(feature['geometry']['coordinates'][0])
            platform = feature['properties']['platform']
            epoch_time = ''
            # Toss out the bad ones...
            if latitude != 0 and longitude != 0:
                position = {"mmsi" :  platform, "longitude" : longitude,
                            "latitude" : latitude,
                            "timestamp" : epoch
                            }
                argo_positions.append(position)

    return argo_positions


def gandalf_to_saildrone():
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-08-09
    Modified:   2022-08-09
    Notes:      Main entry point
                We load up the json files, get the keys and send the data
                to get_last_positions. We get a list of dicts returned, so we
                iterate and append into pos_list so we don't have a list of
                a list of dicts.
    """
    pos_list = []
    v_data = {
                'slocum' : '/data/gandalf/deployments/geojson/local.json',
                'sg' : '/data/gandalf/deployments/geojson/seagliders.json',
                'gdac' : '/data/gandalf/deployments/geojson/gdac.json'
            }
    for key in v_data.keys():
        data_file = (v_data[key])
        try:
            with open(data_file) as json_data:
                jdata = json.loads(json_data.read())
                last_positions = get_last_positions(jdata)
                for lp in last_positions:
                    pos_list.append(lp)
        except ValueError as error:
            logging.warning(error)
    update_sdmp(pos_list)
    pos_list = get_argo_positions()
    update_sdmp(pos_list)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO)


    args = get_cli_args()
    if args['token']:
        generate_auth_token()
    else:
        gandalf_to_saildrone()
