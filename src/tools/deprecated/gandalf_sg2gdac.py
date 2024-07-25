#!/usr/bin/env python3
"""
Author:     robertdcurrier@gmail.com
Created:    2022-06-15
Modified:   2022-08-08
Notes:      Command line and GANDALF integrated tool to convert NetCDF files
            produced by Seagliders to IOOS-compliant GDAC NetCDF format.
            Complete rewrite of AOML script. Dataset creation now uses
            sg_gdac.json configuration file and variables are created
            'on the fly'.

            Francis Bringas wrote the AOML code and deserves credit for
            figuring out what needed to be done to make Seaglider data
            GDAC compliant.  I attempted to follow his logic and implement
            it using standard Python styles and practices.

            I tried to make this code as non-fungible as possible, and keep
            a 100% separation between code and data. Thus, the sg_gdac.json
            configuration file. Unfortunately, there are a few variables that
            don't lend themselves to being part of an interable list --
            trajectory and instrument_ctd. These variables are of
            type 'S1' and need stringtochar conversion. I tried to do this
            via config file settings, but just wound up with a lots of
            'if var == 'trajectory' etc statements. Messy. Cumbersome. It
            seemed better to remove these variables from the config file
            and create them using single-purpose defs. While I would like
            to have ALL variable creation driven from the configuration file
            it just doesn't make sense for the few variables that need
            special treatment. Others may find a better way to do this, and
            if so, I applaud them.

            2022-08-08: Finished V1. Passed GDAC 3.0 compliance checker with
            flying colors.
"""
import sys
import time
import json
import logging
import argparse
import glob
import xarray
from datetime import datetime
import numpy as np
from netCDF4 import Dataset, stringtochar
from natsort import natsorted


def flight_status(vehicle):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-06-01
    Modified:   2022-08-01
    Notes:      Modified to use sg_gdac.json as gandalf_sg2gdac is the
                only GANDALF tool designed to run outside the GANDALF
                ecosystem.
    """
    config = get_sg_config(vehicle)
    status = config['config_settings']['status']
    logging.debug('flight_status(%s): %s', vehicle, status)
    return status


def get_vehicle_config(vehicle):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-06-01
    Modified:   2022-07-27
    Notes:      Now we just use get_vehicle_config -- need to account for
                -c arg so user can point at another config file
    """
    logging.debug("get_vehicle_config(%s)", vehicle)
    data_file = ("/data/gandalf/gandalf_configs/vehicles/%s/ngdac/deployment.json"
                 % vehicle)
    try:
        config = open(data_file, 'r').read()
    except FileNotFoundError as error:
        logging.warning('get_vehicle_config(%s): %s', vehicle, error)
    config = json.loads(config)
    return config


def get_cli_args():
    """
    Author:     robertdcurrier@gmail.com
    Created:    2018-11-06
    Modified:   2022-06-16
    Notes:      One arg: vehicle
    """
    logging.debug('get_cli_args()')
    arg_p = argparse.ArgumentParser()
    arg_p.add_argument("-v", "--vehicle", help="vehicle name",
                       nargs="?", required='True')
    arg_p.add_argument("-c", "--config", help="alternate config file",
                       nargs="?")
    args = vars(arg_p.parse_args())
    return args


def get_sg_config(vehicle):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-06-22
    Modified:   2022-08-01
    Notes:      Gets all SG config info for creating nc files. Vars, etc.
                Added --config option for loading alternate config files
    """
    args = get_cli_args()
    logging.debug('get_sg_config(%s)', vehicle)
    if args["config"]:
        data_file = "%s" % args['config']
    else:
        data_file = ("/data/gandalf/gandalf_configs/vehicles/%s/ngdac/sg_gdac.json"
                     % vehicle)
    try:
        config = open(data_file, 'r').read()
    except FileNotFoundError as error:
        logging.warning('get_sg_config(%s): %s', vehicle, error)
        sys.exit()
    config = json.loads(config)
    gkeys = config['global_attributes'].keys()
    for gkey in gkeys:
        logging.debug("get_sg_config(%s): Global %s", vehicle, gkey)
    return config


def get_sg_files(vehicle):
    """
    Created:    2022-05-12
    Modified:   2022-06-06
    Author:     bob.currier@gcoos.org
    Notes:      Get list of files in data dir.  Update: added status test
                for deployed/recovered
    """
    config = get_sg_config(vehicle)
    status = flight_status(vehicle)

    if status == 'deployed':
        data_dir = config['config_settings']['deployed_sg_nc_files_in']
    if status == 'recovered':
        data_dir = config['config_settings']['recovered_sg_nc_files_in']

    nc_file_glob = "%s/*.nc" % data_dir
    logging.info('get_sg_files(%s): Using glob %s', vehicle, nc_file_glob)
    nc_files = natsorted(glob.glob(nc_file_glob))
    logging.info('get_sg_files(%s) found %d NetCDF files...', vehicle,
                 len(nc_files))
    return nc_files


def create_trajectory(vehicle, dataset, sg_config):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-07-29
    Modified:   2022-07-29
    Notes:      Trajectory is a special case and can't easily be constructed
                by iterating over list of gdac_vars as it is an S1 with
                a stringtochar conversion. Easier to have a stand-alone def
                to handle the few gdac vars like this...
    """
    logging.debug('create_trajectory(%s): Creating Trajectory', vehicle)
    trajectory = sg_config['config_settings']['trajectory_name']
    traj_chars = stringtochar(np.array([trajectory], 'S16'))
    trajectory = dataset.createVariable("trajectory", "S1",
                                        ("traj_strlen",))
    trajectory.cf_role = "trajectory_id"
    trajectory.comment = """A trajectory is a single deployment of a glider
and may span multiple data files."""
    trajectory.long_name = "Trajectory/Deployment Name"
    trajectory[:] = traj_chars
    return dataset


def create_instrument_ctd(vehicle, dataset, sg_config):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-07-29
    Modified:   2022-07-29
    Notes:      instrument_ctd is a special case and can't easily be constructed
                by iterating over list of gdac_vars as it is an S1 with
                a stringtochar conversion. Easier to have a stand-alone def
                to handle the few gdac vars like this...
    """
    logging.debug('create_instrument_ctd(%s)', vehicle)
    instrument_ctd = sg_config['ctd']['instrument_ctd']
    ctd_serial_number = sg_config['ctd']['ctd_serial_number']
    ctd_calib_date = sg_config['ctd']['ctd_calib_date']

    ctd_chars = stringtochar(np.array([instrument_ctd], 'S5'))
    instrument_ctd = dataset.createVariable("instrument_ctd", "S1",
                                            ("string_5",), fill_value = 0)
    instrument_ctd.calibration_date = ctd_calib_date
    instrument_ctd.calibration_report = ctd_calib_date
    instrument_ctd.factory_calibrated = ctd_calib_date
    instrument_ctd.comment = "CTD"
    instrument_ctd.long_name = "Underway Thermosalinograph"
    instrument_ctd.make_model = "Seabird SBE41"
    instrument_ctd.serial_number = ctd_serial_number
    instrument_ctd.platform = "glider"
    instrument_ctd.type = "thermosalinograph"
    instrument_ctd[:] = ctd_chars
    return dataset


def create_profile(dataset, profile):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-07-29
    Modified:   2022-08-03
    Notes:      profile is a special case and can't easily be constructed
                by iterating over list of gdac_vars as it must be updated
                with new data each yo.  Easier to have a stand-alone def
                to handle the few gdac vars like this...
    """
    logging.info('create_profile(%d)' % profile)
    # Set time, lat and lon at mean of profile using GDAC naming convention
    lat = dataset.variables['lat'][:].mean()
    lon = dataset.variables['lon'][:].mean()
    sgtime = dataset.variables['time'][:].mean()
    dataset.variables['profile_id'][:] = profile
    dataset.variables['profile_time'][:] = sgtime
    dataset.variables['profile_lat'][:] = lat
    dataset.variables['profile_lon'][:] = lon
    return dataset


def create_gdac_vars(dataset, sg_config):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-07-28
    Modified:   2022-08-03
    Notes:      Populates vars needed by GDAC using config file values.
                Trajectory and instrument_ctd are special cases,
                with S1, stringtochar etc, so it is easier to create them
                with one-off defs instead of trying to deal with them in the
                the gdac_var config file section. For the majority of the
                gdac_vars we can just iterate over the config file.
                Note: Fixed bug as I had included ref var of 'time' which the
                gdac_vars do not need.
    """
    for gdac_var in sg_config['gdac_variables']:
        logging.debug('create_gdac_vars(): Creating var %s', gdac_var)
        var_type = sg_config['gdac_variables'][gdac_var]['var_def']['var_type']
        var_fill = sg_config['gdac_variables'][gdac_var]['var_def']['var_fill']

        logging.debug('create_gdac_vars(): Creating %s', gdac_var)
        # QC vars must ref time, all others not...
        if '_qc' in gdac_var:
            temp_name = dataset.createVariable(gdac_var, var_type, ("time",),
                                               fill_value=var_fill)
        else:
            temp_name = dataset.createVariable(gdac_var, var_type,
                                                fill_value=var_fill)
        for record in sg_config['gdac_variables'][gdac_var]['var_keys']:
            logging.debug('create_gdac_vars(): adding %s to %s', record,
                          gdac_var)
            value = sg_config['gdac_variables'][gdac_var]['var_keys'][record]
            if isinstance(value, str):
                logging.debug('STRING', gdac_var, record, value)
                command = "temp_name.%s = '%s'" % (record, value)
                logging.debug(gdac_var, command)
            else:
                logging.debug('NOT STRING', gdac_var, record, value)
                command = "temp_name.%s = %d" % (record, value)
                logging.debug(gdac_var,command)
            exec(command)
    return dataset


def create_global_vars(vehicle, dataset, sg_config, epoch):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-07-18
    Modified:   2022-08-08
    Notes:      Add globals using dynamic variable names. We have to use
    exec() for this, as there is no other way to add variables on the fly
    as NetCDF does not support assignment. This is a hack, but it
    drastically reduces the code for creating globals.

    TO DO: We need to have access to the timestamp here so we can set
    date_created, date_issued, date_modified, history, id and title.
    """
    logging.debug('create_global_vars()')
    # Fixed global vars
    for glob_att in sg_config['global_attributes']:
        logging.debug('create_global_vars() ATTRIBUTE: %s', glob_att)
        glob_att_var = sg_config['global_attributes'][glob_att]
        logging.debug('create_global_vars() VALUE: %s', glob_att_var)
        command = "dataset.%s = '%s'" % (glob_att, glob_att_var)
        logging.debug('create_global_vars() COMMAND: %s', command)
        exec(command)
    # Timestamp dependent global vars
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime(epoch))
    dataset.date_created = timestamp
    dataset.date_issued = timestamp
    dataset.date_modified = timestamp
    title_ts = time.strftime('%Y%m%dT%H%M%S', time.localtime(epoch))
    title = "%s-%s" % (vehicle, title_ts)
    dataset.title = title
    dataset.id = title
    version = sg_config['global_attributes']['format_version']
    dataset.history = 'Created on %s using %s' % (timestamp, version)
    return dataset


def create_local_vars(dataset, sg_config):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-07-18
    Modified:   2022-07-29
    Notes:      Add locals using dynamic variable names. We have to use
    exec() for this, as there is no other way to add variables on the fly
    as NetCDF does not support assignment. This is a hack, but it
    drastically reduces the code for creating variables.
    """
    logging.debug('create_local_vars()')
    name_map = sg_config['sg_to_gdac_names']

    for local_var in sg_config['sg_variables']:
        logging.debug('create_local_vars(): Creating var %s', local_var)
        # Get variable type and fill from config file so we create proper var
        var_type = sg_config['sg_variables'][local_var]['var_def']['var_type']
        var_fill = sg_config['sg_variables'][local_var]['var_def']['var_fill']
        # JSON doesn't support nan, so we hack from text to np.nan
        if var_fill == 'nan':
            var_fill = np.nan
        # Only used for lat/latitude and lon/longitude
        if local_var in name_map:
            gdac_var = name_map[local_var]
        else:
            gdac_var = local_var

        temp_name = dataset.createVariable(gdac_var, var_type, ("time",),
                                           fill_value=var_fill)
        for record in sg_config['sg_variables'][local_var]['var_keys']:
            logging.debug('create_local_vars(): adding %s', gdac_var)
            value = sg_config['sg_variables'][local_var]['var_keys'][record]
            if isinstance(value, str):
                logging.debug('STRING', gdac_var, record, value)
                command = "temp_name.%s = '%s'" % (record, value)
                logging.debug(gdac_var, command)
            else:
                logging.debug('NOT STRING', gdac_var, record, value)
                command = "temp_name.%s = %d" % (record, value)
                logging.debug(gdac_var,command)
            exec(command)
    return dataset


def read_sg_nc(vehicle, sgfile):
    """
    Created:    2022-07-26
    Modified:   2022-07-26
    Author:     bob.currier@gcoos.org
    Notes:      Uses xarray to load vehicle-generated NetCDF files
    """
    logging.debug('read_sg_nc(%s)', sgfile)
    try:
        sg_ds = xarray.open_dataset(sgfile, decode_cf=True, mask_and_scale=False,
                                    decode_times=False)
    except:
        logging.warning('read_sg_nc(): Failed to read %s', sgfile)
        sys.exit()

    return sg_ds


def create_u_and_v(dataset, sg_ds):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-08-03
    Modified:   2022-08-03
    Notes:      Get u and v from seaglider dataset and assign to GDAC dataset
    """
    u = sg_ds.variables['depth_avg_curr_east'].values
    v = sg_ds.variables['depth_avg_curr_north'].values
    dataset.variables['u'][:] = u
    dataset.variables['v'][:] = v
    return dataset


def set_no_qc_vars(dataset, sg_ds):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-08-03
    Modified:   2022-08-03
    Notes:      These vars don't have qc so we set to zero or one
                They are scalars so no dim needed
    """
    dataset.variables['profile_time_qc'][:] = 0
    dataset.variables['profile_lat_qc'][:] = 0
    dataset.variables['profile_lon_qc'][:] = 0
    dataset.variables['time_uv_qc'][:] = 0
    dataset.variables['lat_uv_qc'][:] = 0
    dataset.variables['lon_uv_qc'][:] = 0
    dataset.variables['lat_qc'][:] =  0
    dataset.variables['lon_qc'][:] =  0
    dataset.variables['pressure_qc'][:] =  0
    dataset.variables['depth_qc'][:] =  0
    dataset.variables['density_qc'][:] =  0
    dataset.variables['u_qc'][:] = 1
    dataset.variables['v_qc'][:] = 1
    return dataset


def set_qc_vars(dataset, sg_ds, begin, end):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-08-03
    Modified:   2022-08-08
    Notes:      Map SG vars that have QC to GDAC vars
                These are dimensioned so we need fill values mapped
    """
    # The following are provided by the SG so we can map
    qc = list(map(int, sg_ds.variables['temperature_qc'][begin:end]))
    dataset.variables['temperature_qc'][:] = qc
    qc = list(map(int, sg_ds.variables['conductivity_qc'][begin:end]))
    dataset.variables['conductivity_qc'][:] = qc
    qc = list(map(int, sg_ds.variables['salinity_qc'][begin:end]))
    dataset.variables['salinity_qc'][:] = qc
    # GDAC vars so we have to fill
    fill = [0 for i in range(end-begin)]
    dataset.variables['time_qc'][:] =  fill
    return dataset


def create_downcast_nc(vehicle, sg_ds, profile):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-07-27
    Modified:   2022-08-01
    Notes:      Changed to use config_settings in sg_gdac.json
    """
    sg_config = get_sg_config(vehicle)
    status = flight_status(vehicle)

    if status == 'deployed':
        nc_dir = sg_config['config_settings']['deployed_gdac_nc_files_out']
        suffix = 'rt'
    if status == 'recovered':
        nc_dir = sg_config['config_settings']['recovered_gdac_nc_files_out']
        suffix = 'delayed'

    ctd_depth = sg_ds.variables['ctd_depth'][:]

    down_count = int(ctd_depth.argmax() + 1)
    depth_down = ctd_depth[0 : down_count]
    down_epoch = int(sg_ds.variables['ctd_time'][:][0])
    up_count = len(ctd_depth)
    up_epoch = int(sg_ds.variables['ctd_time'][:][-1])
    depth_up = ctd_depth[down_count : up_count]
    date_created = sg_ds.date_created

    timestamp = time.strftime('%Y%m%dT%H%M%S', time.localtime(down_epoch))
    fname = '%s/%s-%s_%s.nc' % (nc_dir, vehicle, timestamp, suffix)
    logging.info('create_downcast_nc(%s): Creating %s', vehicle, fname)
    dataset = Dataset(fname, "w", format="NETCDF4_CLASSIC")
    num_dim = len(depth_down)
    sgtime = dataset.createDimension("time", num_dim)
    traj_strlen = dataset.createDimension("traj_strlen", 16)
    string_5 = dataset.createDimension("string_5", 5)

    # Set creation date/issued/modfied
    dataset.date_created = date_created
    dataset.date_issued = date_created
    dataset.date_modified = date_created
    # set platform type to 0
    dataset.variables['platform'] = 0
    # Create metadata, gdac_vars, global vars, local vars
    dataset = create_global_vars(vehicle, dataset, sg_config, down_epoch)
    dataset = create_local_vars(dataset, sg_config)
    dataset = create_gdac_vars(dataset, sg_config)
    # Only used for lat/latitude and lon/longitude
    name_map = sg_config['sg_to_gdac_names']
    # Assign data to variables

    for sg_var in sg_config['sg_variables']:
        if sg_var in name_map:
            gdac_var = name_map[sg_var]
        else:
            gdac_var = sg_var
        command = "%s_down = sg_ds.variables['%s'][0:down_count]" % (gdac_var,
                                                                     sg_var)
        exec(command)
        command = ("dataset.variables['%s'][:] = %s_down[:]" %
                   (gdac_var, gdac_var))
        exec(command)
    # Create variables that don't have a one-to-one with SG data
    dataset = create_trajectory(vehicle, dataset, sg_config)
    dataset = create_instrument_ctd(vehicle, dataset, sg_config)
    dataset = create_profile(dataset, profile)
    dataset = create_u_and_v(dataset, sg_ds)
    dataset = set_no_qc_vars(dataset, sg_ds)
    dataset = set_qc_vars(dataset, sg_ds, 0, down_count)
    dataset.close()


def create_upcast_nc(vehicle, sg_ds, profile):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-07-27
    Modified:   2022-08-01
    Notes:      Changed to use config_settings in sg_gdac.json
    """
    sg_config = get_sg_config(vehicle)
    status = flight_status(vehicle)

    if status == 'deployed':
        nc_dir = sg_config['config_settings']['deployed_gdac_nc_files_out']
        suffix = 'rt'
    if status == 'recovered':
        nc_dir = sg_config['config_settings']['recovered_gdac_nc_files_out']
        suffix = 'delayed'
    ctd_depth = sg_ds.variables['ctd_depth'][:]
    down_count = int(ctd_depth.argmax() + 1)
    up_count = len(ctd_depth)
    depth_down = ctd_depth[0 : down_count]
    depth_up = ctd_depth[down_count : up_count]
    up_epoch = int(sg_ds.variables['ctd_time'][:][-1])
    date_created = sg_ds.date_created
    timestamp = time.strftime('%Y%m%dT%H%M%S', time.localtime(up_epoch))
    fname = '%s/%s-%s_%s.nc' % (nc_dir, vehicle, timestamp, suffix)
    num_dim = len(depth_up)
    logging.info('create_upcast_nc(%s): Creating %s', vehicle, fname)
    dataset = Dataset(fname, "w", format="NETCDF4_CLASSIC")
    sgtime = dataset.createDimension("time", num_dim)
    traj_strlen = dataset.createDimension("traj_strlen", 16)
    string_5 = dataset.createDimension("string_5", 5)

    # Set date_created/issued/modified
    dataset.date_created = date_created
    dataset.date_issued = date_created
    dataset.date_modified = date_created
    # Set platform type to 0
    dataset.variables['platform'] = 0
    # Create metadata, gdac_vars, global vars, local vars
    dataset = create_global_vars(vehicle, dataset, sg_config, up_epoch)
    dataset = create_local_vars(dataset, sg_config)
    dataset = create_gdac_vars(dataset, sg_config)

    # Only used for lat/latitude and lon/longitude
    name_map = sg_config['sg_to_gdac_names']
    # Assign data to variables
    for sg_var in sg_config['sg_variables']:
        if sg_var in name_map:
            gdac_var = name_map[sg_var]
        else:
            gdac_var = sg_var
        command = ("%s_up = sg_ds.variables['%s'][down_count:up_count]" %
                   (gdac_var, sg_var))
        exec(command)
        command = ("dataset.variables['%s'][:] = %s_up[:]" % (gdac_var,
                                                              gdac_var))
        exec(command)

    # Create variables that don't have a one-to-one with SG data
    dataset = create_trajectory(vehicle, dataset, sg_config)
    dataset = create_instrument_ctd(vehicle, dataset, sg_config)
    dataset = create_profile(dataset, profile)
    dataset = create_u_and_v(dataset, sg_ds)
    dataset = set_no_qc_vars(dataset, sg_ds)
    dataset = set_qc_vars(dataset, sg_ds, down_count, up_count)
    dataset.close()


def clean_files(vehicle):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-08-01
    Modified:   2022-08-01
    Notes:      Wipes output directory of files to ensure clean data
    """
    pass


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
    sg_config = get_sg_config(vehicle)
    validate_vars = sg_config['validate_vars']
    for var in validate_vars:
        logging.debug('validate_ds(): Checking for %s', var)
    if not var in sg_ds.variables:
        logging.warning('validate_ds(%s): %s failed validation for %s', vehicle,
                        sgfile, var)
        return False
    return True


def gandalf_sg2gdac(vehicle):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-06-01
    Modified:   2022-07-28
    Notes:      Primary entry point
    """

    logging.info('gandalf_sg2gdac(%s)', vehicle)
    sg_files = get_sg_files(vehicle)
    # Set initial profile number to 1 and increment.  Let's rock and roll...
    profile = 1
    for sgfile in sg_files:
        sg_ds = read_sg_nc(vehicle, sgfile)
        validate = validate_ds(sgfile, vehicle, sg_ds)
        if validate:
            create_downcast_nc(vehicle, sg_ds, profile)
            profile += 1
            create_upcast_nc(vehicle, sg_ds, profile)
            profile += 1
        else:
            logging.warning('gandalf_sg2gdac(): %s validation error', sgfile)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO)
    gandalf_sg2gdac(get_cli_args()['vehicle'])
