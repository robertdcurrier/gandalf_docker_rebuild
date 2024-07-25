#!/usr/bin/env python3
"""
Name:       gandalf_sg2csv.py
Created:    2022-05-11
Modified:   2023-01-24
Author:     bob.currier@gcoos.org
Inputs:     Vehicle data files in NetCDF format
Outputs:    GDAC-compliant NetCDF files with GANDALF expansion
Notes:      Starting with CICESE but need to make vehicle independent
            Using config file to keep main body of code clean. Config file
            is JSON text and standard deployment.json structure.
            2022-05-18: rdc began rework of CICESE code to fit standard SG
            deployments where data comes as single NetCDF files from the
            SG BaseStation.
            2023-01-24: Migrating to MongoDB for interim data storage as we
            have been having shape-shifter problems. Now the process is
            Drop_DB -> Create_DB -> .nc -> Mongo -> CSV on each run
"""
import sys
import os
import json
import logging
import time
import xarray
import netCDF4 as nc
import glob
import argparse
import numpy as np
import pandas as pd
from natsort import natsorted
from gandalf_utils import get_vehicle_config, flight_status
from gandalf_mongo import connect_mongo, insert_record


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


def read_netcdf(vehicle, nc_file):
    """
    Name:       read_netcdf
    Created:    2022-05-12
    Modified:   2022-05-17
    Author:     bob.currier@gcoos.org
    Notes:      Uses xarray to load vehicle-generated NetCDF files
    """
    logging.debug('read_netcdf(%s, %s)' % (vehicle, nc_file))
    try:
        df1 = xarray.open_dataset(nc_file, decode_cf=True, mask_and_scale=True,
                                  decode_times=False)
        logging.debug("read_netcdf(%s): dims %s", vehicle, df1.dims)
    except:
        logging.warning("read_netcdf(%s, %s): Failed to open file.",
                        vehicle, nc_file)
    return df1




def validate_ds(sgfile, vehicle, sg_ds):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-08-03
    Modified:   2022-08-03
    Notes:      Make sure all vars in config are in sg_ds. We've seen some
                corrupt files that are missing variables. For now we're just
                using ctd_depth... and we need to add validate_vars to the
                config file so we aren't hardwired here...
    """
    config = get_vehicle_config(vehicle)
    validate_vars = config['gandalf']['validate_vars']
    for var in validate_vars:
        logging.debug('validate_ds(): Checking for %s', var)
    if not var in sg_ds.variables:
        logging.warning('validate_ds(%s): %s failed validation for %s', vehicle,
                        sgfile, var)
        return False
    return True


def drop_dims(vehicle, ds1, keep_dim):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-11-01
    Modified:   2023-01-30
    Notes:      Deal with Legato RBR and SciConn data. Shit be weird, like
                Marky Mark and the Funky Bunch.
    2023-01-30
    Okay, we are trying a new method of dealing with different sized dims. 
    We will parse dim by dim, inserting into MongoDB. Then we'll let Mongo
    deal with aligning all the data when the CSV is generated... we'll see
    if this works. We'll need a list of dims of interest to iterate over, and 
    we should probably still whack all the unecessary sensors. For now we'll 
    hardwire the dim list and when it's working we'll move the the config file.
    """

    all_dims = ds1.dims
    for dim in all_dims:
        if dim != keep_dim:
            ds1 = ds1.drop_dims(dim)
    return ds1


def sg_MDIMS_parse_files(vehicle, sg_files):
    """
    Name:       sg_MDIMS_parse_files
    Created:    2023-01-30
    Modified:   2023-01-30
    Author:     bob.currier@gcoos.org
    Notes:      Now using totally different methodolgy. Instead of trying to process
    all dims at once (causing massive memory overflow when creating dataframes) we
    have a list of keep_dims. We iterate over the list, creating a temporary dataset,
    passing the dim to keep to drop_dims which drops all other dims. We then interate
    over the single dim, writing to MongoDB. We then repeat with the next dim in the
    keep_dim list. The final result is a single MongoDB collection with all sensors of
    interest, all timestamped so that Mongo can align them on time and write to a CSV.

    """
    logging.info('sg_MDIMS_parse_files(%s): Processing NetCDF files...' %
                 vehicle)

    config = get_vehicle_config(vehicle)
    sg_sensors = config['gandalf']['sg_sensors']
    df = pd.DataFrame(columns=sg_sensors)
    client = connect_mongo()
    db = client.gandalf
    logging.info('sg_MDIMS_parse_files(%s): Purging sgdata', vehicle)
    db.sgdata.drop()

    filenum = 0
    for ifile in sg_files:
        df1 = []
        basename = os.path.basename(ifile)
        logging.info('sg_MDIMS_parse_files(%s): Parsing %s' % (vehicle, basename))
        logging.debug('sg_MDIMS_parse_files(%s) Sensors: %s' % (vehicle, sg_sensors))
        ds1 = read_netcdf(vehicle, ifile)
        
        # 2023-01-11 brought this in from gandalf_sg2gdac to validate files
        valid = validate_ds(ifile, vehicle, ds1)
        if not valid:
            logging.info('sg_MDIMS_parse_files(%s): Invalid .nc file %s',
                         vehicle, ifile)
            continue
      
        # Put these in config settings
        keep_dims = ['ctd_data_point', 'aa4831_data_point']
        try:
            for keep_dim in keep_dims:
                ds_tmp = drop_dims(vehicle, ds1, keep_dim)
                df1 = ds_tmp.to_dataframe()
                #
                #
                # WE GOTTA SLIM DF IT HERE OR IT BE TFB!
                # 
                #
                #
                sgjson = json.loads(df1.to_json(orient='records'))
                logging.debug('sg_MDIMS_parse_files(%s): Processing %s', vehicle,
                             ds_tmp.dims)
                for row in sgjson:
                    result = db.sgdata.insert_one(row)
            sys.exit
        except:
            logging.warning('sg_MDIMS_parse_files(%s): Missing dims', vehicle)
            continue


def get_sg_files(vehicle):
    """
    Name:       get_sg_files
    Created:    2022-05-12 PROCESS

    Modified:   2022-06-06
    Author:     bob.currier@gcoos.org
    Notes:      Get list of files in data dir.  Update: added status test
                for deployed/recovered
    """
    config = get_vehicle_config(vehicle)

    status = flight_status(vehicle)
    if status == 'deployed':
        data_dir = config['gandalf']['deployed_data_dir']
        plot_dir = config['gandalf']['plots']['deployed_plot_dir']
    if status == 'recovered':
        data_dir = config['gandalf']['post_data_dir_root']
        plot_dir = config['gandalf']['plots']['postprocess_plot_dir']

    nc_file_glob = data_dir + '/binary_files/nc/*.nc'
    logging.info('get_sg_files(%s): Using glob %s' %(vehicle, nc_file_glob))
    nc_files = natsorted(glob.glob(nc_file_glob))
    logging.info('get_sg_files(%s) found %d NetCDF files...' %
                 (vehicle, len(nc_files)))
    if len(nc_files) == 0:
        logging.warning("get_sg_files(%s): No files found. Skipping...", vehicle)
        return False
    return(nc_files)


def sg_write_csv(vehicle):
    """
    """
    logging.info('sg_write_csv(%s)', vehicle)
    config = get_vehicle_config(vehicle)

    status = flight_status(vehicle)
    if status == 'deployed':
        data_dir = config['gandalf']['deployed_data_dir']
    if status == 'recovered':
        data_dir = config['gandalf']['post_data_dir_root']

    client = connect_mongo()
    db = client.gandalf
    df = pd.DataFrame(list(db.sgdata.find()))
    fname = ('%s/processed_data/sensors.csv' % data_dir)
    csv = df.to_csv(fname, index=False)


def gandalf_sg2csv(vehicle):
    """
    Name:       gandalf_sg2csv
    Created:    2022-05-11
    Modified:   2022-05-18
    Author:     bob.currier@gcoos.org
    Notes:      Main entry point
                Now iterating over all matched files after orphan test
    """

    logging.info('gandalf_sg2csv(%s)...' % vehicle)
    config = get_vehicle_config(vehicle)
    sg_files = get_sg_files(vehicle)
    if sg_files:
        sg_MDIMS_parse_files(vehicle, sg_files)
    sg_write_csv(vehicle)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    args = get_cli_args()
    vehicle = args['vehicle']
    gandalf_sg2csv(vehicle)
