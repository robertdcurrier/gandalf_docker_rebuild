#!/usr/bin/env python3
"""
Name:       gandalf_csv_utils.py
Created:    2016-09-05
Modified:   2023-10-17
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
logging.basicConfig(level=logging.INFO)


def dinkum_convert(gps_lon, gps_lat):
    """
    Name:       dinkum_convert
    Author:     bob.currier@gcoos.org
    Created:    2015-07-22
    Modified:   2015-07-22
    Inputs:     lon, lat in dddd.mm
    Outputs:    lon, lat in dd.ddd
    """
    getcontext().prec = 6
    gps_lon = Decimal(gps_lon)
    gps_lat = Decimal(gps_lat)
    lat_int = int((gps_lat / Decimal(100.0)))
    lon_int = int((gps_lon / Decimal(100.0)))
    lat = Decimal((lat_int + (gps_lat - (lat_int * 100)) / Decimal(60.0)))
    lon = Decimal((lon_int + (gps_lon - (lon_int * 100)) / Decimal(60.0)))
    return lon, lat


def get_deployment_status_all():
    """
    Name:       get_deployment_status_all
    Author:     bob.currier@gcoos.org
    Created:    2022-06-01
    Modified:   2022-06-01
    Notes:      New version uses deployment.json files vs single gandalf.cfg
                We now iterate over all deployment.json files looking for
                vehicles with status of "deployed".  This allows us to not
                have multiple config files for each vehicle as well as
                providing better support for multiple vehicle types.
    """
    # This we have to hardwire.  All other settings come from config files
    gandalf_config_dir = '/data/gandalf/gandalf_configs/vehicles'
    deployed = []
    vehicles = [ f.path for f in os.scandir(gandalf_config_dir) if f.is_dir() ]
    for vehicle in vehicles:
        config_file = '%s/ngdac/deployment.json' % vehicle
        with open(config_file) as cfile:
            gandalf_config = json.loads(cfile.read())
            vehicle = gandalf_config['gandalf']['vehicle']
            status = gandalf_config['gandalf']['status']
            vtype = gandalf_config['gandalf']['vehicle_type']
            vdata = gandalf_config['gandalf']['vehicle_data']
            vsource = gandalf_config['gandalf']['data_source']
            if status == 'deployed':
                deployed.append([vehicle, vtype, vdata, vsource])
    return deployed


def flight_status(vehicle):
        """
        Name:       flight_status
        Author:     robertdcurrier@gmail.com
        Created:    2022-06-01
        Modified:   2022-06-15
        Notes:      Now we just use get_vehicle_config
        """
        config = get_vehicle_config(vehicle)
        status = config['gandalf']['status']
        logging.debug('flight_status(%s): %s' % (vehicle, status))
        return status


def get_deployed_slocum(deployed):
    """
    Name:       get_deployed_local
    Author:     robertdcurrier@gmail.com
    Created:    2022-06-01
    Modified:   2022-06-01
    Notes:      Gets all deployed Slocum gliders that we have
                direct access to logs, sbd and tbd files.
                Now using single deployed array as we migrate towards
                parsing deployment.json files instead of using gandalf.cfg.
                We should be using dicts instead of arrays, but arrays are
                working for now. We'll move to dicts as we progress.
    """
    logging.info("get_deployed_slocum()")
    slocum_gliders = []
    for vehicle in deployed:
        if vehicle[1] == 'slocum' and vehicle[2] == 'local':
            slocum_gliders.append(vehicle[0])
    return slocum_gliders


def get_deployed_saildrones(deployed):
    """
    Name:       get_deployed_saildrones
    Author:     robertdcurrier@gmail.com
    Created:    2022-08-22
    Modified:   2022-08-22
    Notes:      Gets all deployed Saildrones via PMEL ERDDAP
    """
    logging.info("get_deployed_saildrones()")
    saildrones = []
    for vehicle in deployed:
        if vehicle[1] == 'saildrone' and vehicle[3] == 'PMEL':
            saildrones.append(vehicle[0])
    return saildrones


def get_deployed_gdac(deployed):
    """
    Name:       get_deployed_gdac
    Author:     robertdcurrier@gmail.com
    Created:    2022-06-01
    Modified:   2022-06-01
    Notes:      Gets all deployed Slocum gliders that we have
                direct access to logs, sbd and tbd files.
                Now using single deployed array as we migrate towards
                parsing deployment.json files instead of using gandalf.cfg.
                We should be using dicts instead of arrays, but arrays are
                working for now. We'll move to dicts as we progress.
    """
    logging.info("get_deployed_gdac()")
    gdac_gliders = []
    for vehicle in deployed:
        if vehicle[3] == 'IOOS GDAC':
            gdac_gliders.append(vehicle[0])
    return gdac_gliders


def get_deployed_seagliders(deployed):
    """
    Name:       get_deployed_seaglider
    Author:     robertdcurrier@gmail.com
    Created:    2022-06-01
    Modified:   2022-06-02
    Notes:      Gets all deployed Seagliders that we have
                direct access NetCDF files.
    """
    logging.info("get_deployed_seaglider()")
    seagliders = []
    for vehicle in deployed:
        if vehicle[1] == 'seaglider' and vehicle[2] != 'erddap':
            seagliders.append(vehicle[0])
    return seagliders


def get_vehicle_config(vehicle):
    """
    Sorta evident...
    Update: 2023-05023  Added soft landing if vehicle path not found. Prior to this we
    just brain farted and died a screaming death...

    """
    logging.debug("get_vehicle_config(%s)" % vehicle)
    # get config debug for each vehicle
    data_file = ("/data/gandalf/gandalf_configs/vehicles/%s/ngdac/deployment.json"
                 % vehicle)
    try:
        config = open(data_file,'r').read();
    except FileNotFoundError as e:
        logging.warning('get_vehicle_config(%s): %s' % (vehicle, e))
        logging.warning('Aborting...')
        sys.exit()
    config = json.loads(config)
    return config


def get_sensor_config(vehicle):
    """
    Sorta evident...
    """
    # get config debug for sensors
    logging.debug('get_sensor_config(%s)' % vehicle)
    data_file = ("/data/gandalf/gandalf_configs/vehicles/%s/sensors.json") % vehicle
    with open(data_file, 'r') as f:
        sensors = json.load(f)
    return sensors


if __name__ == '__main__':
    """
    For command line use
    """
    logging.basicConfig(level=logging.WARNING)
    if len(sys.argv) != 2:
        logging.warning("Usage: gandalf_utils vehicle")
        sys.exit()
    else:
        pass
