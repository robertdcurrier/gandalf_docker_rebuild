#!/usr/bin/env python3
"""
Name:       gandalf_cicese_nc.py
Created:    2022-05-11
Modified:   2022-05-12
Author:     bob.currier@gcoos.org
Inputs:     Vehicle data files in NetCDF format
Outputs:    GDAC-compliant NetCDF files with GANDALF expansion
Notes:      Starting with CICESE but need to make vehicle independent
            Using config file to keep main body of code clean. Config file
            is JSON text.
"""
import sys
import json
import logging
import time
import xarray
import glob
import argparse
from natsort import natsorted
import numpy as np
import pandas as pd

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


def get_vehicle_config(vehicle):
    """
    Sorta evident...
    """
    logging.debug("get_vehicle_config(%s)" % vehicle)
    # get config debug for each vehicle
    data_file = ("/data/gandalf/gandalf_configs/%s/ngdac/deployment.json"
                 % vehicle)
    try:
        config = open(data_file,'r').read();
    except:
        logging.warning('get_vehicle_config(%s): Could not open config file' %
                        vehicle)
        sys.exit()
    try:
        config = json.loads(config)
        return config
    except ValueError:
        logging.warning('get_vehicle_config(%s): Corrupt JSON file' %
                        vehicle)
        sys.exit()


def read_netcdf(vehicle, nc_file):
    """
    Name:       read_netcdf
    Created:    2022-05-12
    Modified:   2022-05-17
    Author:     bob.currier@gcoos.org
    Notes:      Uses xarray to load vehicle-generated NetCDF files
    """
    config = get_vehicle_config(vehicle)
    data_dir = config['gandalf']['post_data_dir_root']
    full_path = '%s/%s' % (data_dir, nc_file)
    logging.info('read_netcdf(%s)' % full_path)
    data_structure = xarray.open_dataset(full_path)
    return data_structure


def parse_files_to_csv(vehicle, pro_files, traj_files):
    """
    Name:       parse_files_to_csv
    Created:    2022-05-12
    Modified:   2022-05-17
    Author:     bob.currier@gcoos.org
    Notes:      combine profile and trajectory files into one DF by extracting
                select variables from xarray data, converting to pandas df
                then exporting to standard GANDALF sensors.csv file.
    """
    logging.info('parse_files(%s): Merging profiles and trajectories' %
                 vehicle)

    config = get_vehicle_config(vehicle)
    profile_sensors = config['gandalf']['profile_sensors']
    trajectory_sensors = config['gandalf']['trajectory_sensors']
    df = []
    findex = 0
    for ifile in pro_files:
        logging.debug('Parsing %s and %s' % (ifile, traj_files[findex]))
        df1 = xarray.open_dataset(ifile, decode_cf=True, mask_and_scale=False,
                                  decode_times=False)
        df2 = xarray.open_dataset(traj_files[findex], decode_cf=True,
                                  mask_and_scale=False, decode_times=False)

        """ Need to automate this using vars from config file """
        # Profile
        lat = df1.profile_lat.data
        lon = df1.profile_lon.data
        # Trajectory
        ts = df2.time.data
        depth = df2.depth.data
        salinity = df2.salinity.data
        temperature = df2.temperature.data
        dissolved_oxygen = df2.dissolved_oxygen.data
        chlorophyll_a = df2.chlorophyll_a.data
        cdom = df2.CDOM.data
        scatter = df2.Scatter.data

        record = 0
        for row in ts:
            df.append([ts[record], depth[record], temperature[record],
                      salinity[record], dissolved_oxygen[record],
                      chlorophyll_a[record], cdom[record], scatter[record]])
            record+=1
        findex+=1
    header = config['gandalf']['csv_header']
    logging.debug('parse_files_to_csv(%s): Using %s as header' % (vehicle,
                                                                  header))
    df = pd.DataFrame(df, columns=header)
    return df


def get_files(vehicle):
    """
    Name:       get_files
    Created:    2022-05-12
    Modified:   2022-05-12
    Author:     bob.currier@gcoos.org
    Notes:      Get list of profile and trajectory files in data dir
                Return as two lists
    """
    config = get_vehicle_config(vehicle)
    data_dir = config['gandalf']['post_data_dir_root']
    pro_file_glob = data_dir + '/profiles/*profile*.nc'
    traj_file_glob = data_dir + '/trajectories/*trajectory*.nc'
    pro_files = natsorted(glob.glob(pro_file_glob))
    traj_files = natsorted(glob.glob(traj_file_glob))
    logging.info('get_files(%s) found %d profiles and %d trajectories' %
                 (vehicle, len(pro_files), len(traj_files)))
    return(pro_files, traj_files)


def check_orphans(pro_files, traj_files):
    """
    Name:       check_orphans
    Created:    2022-05-16
    Modified:   2022-05-16
    Author:     bob.currier@gcoos.org
    Notes:      Make sure each profile file has a matching trajectory file.For
                now we just match lengths. We need to do a one-for-one match
                to make this more robust.
    """
    pro_len = len(pro_files)
    traj_len = len(traj_files)
    if pro_len == traj_len:
        status = True
        logging.info('check_orphans(): %s' % status)
        return status
    else:
        status = False
        logging.info('check_orphans(): %s' % status)
        return status




def gandalf_cicese_nc():
    """
    Name:       gandalf_sg2nc
    Created:    2022-05-11
    Modified:   2022-05-16
    Author:     bob.currier@gcoos.org
    Notes:      Main entry point
                Now iterating over all matched files after orphan test
    """
    args = get_cli_args()
    vehicle = args['vehicle']
    logging.info('gandalf_cicese_nc(%s)...' % vehicle)
    config = get_vehicle_config(vehicle)
    (pro_files, traj_files)  = get_files(vehicle)
    if check_orphans(pro_files, traj_files):
        df = parse_files_to_csv(vehicle, pro_files, traj_files)
        # Hack to replace CICESE use of -999 to indicate NaN
        df = df.replace(-999.000000, np.nan)
        outfile = config['gandalf']['post_sensors_csv']
        logging.info('gandalf_cicese_nc(%s): Writing CSV' % vehicle)
        try:
            csv = df.to_csv(outfile, index=False,na_rep='NaN')
        except IOError:
            logging.warning('gandalf_cicese_nc(%s): Failed to write CSV' %
                            vehicle)

    else:
        logging.warning('gandalf_cicese_nc(): Failed orphan test. Exiting.')
        sys.exit()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    gandalf_cicese_nc()
