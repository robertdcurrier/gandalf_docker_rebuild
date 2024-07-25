#!/usr/bin/env python3
"""
Author:     xiao.qi@tamu.edu
Created:    2024-07-05
Modified:   2024-07-09
Notes:      This module sets up latitude and longitude range and horizontal
            resolution using command-line arguments, retrieves the latest daily
            average or latest single time current velocity HYCOM GLBv0.08 data
            for the specified area from the HYCOM netCDF dataset, converts it
            for Leaflet-velocity usage, and saves it to a JSON file.

Example:
$ python hycom_streamlines.py -la0 1900 -la1 3100 -lo0 2900 -lo1 4200 -s 3 -m F
$ python hycom_streamlines.py -la0 2200 -la1 3001 -lo0 3200 -lo1 4000 -s 5 -m T

References: HYCOM (https://www.hycom.org/dataserver/gofs-3pt1/analysis)
            Leaflet-velocity (https://github.com/onaci/leaflet-velocity)
"""
import argparse
from datetime import datetime
from datetime import timedelta
import json
import logging
import time
from netCDF4 import Dataset  # pylint: disable=no-name-in-module
from netCDF4 import num2date  # pylint: disable=no-name-in-module
import numpy as np

# The range of latitude indices is [0, 4251].
# Index 0 corresponds to -80.0 degrees; Index 4250 corresponds to 90.0 degrees.
# Each step represents a 0.04 degree change in latitude.
LAT_START = 1900  # 8.0 degrees
LAT_END = 3100  # 40.04 degrees

# The range of longitude indices is [0, 4500].
# Index 0 corresponds to 0.0 degrees; Index 4499 corresponds to 359.92 degrees.
# Each step represents a 0.08 degree change in longitude.
LON_START = 2900  # 256.0 degrees
LON_END = 4200  # 320.0 degrees

# Step size for latitude and longitude ranges; must be an integer
# A higher step_size value results in a lower horizontal resolution
STEP_SIZE = 5

# True to use daily mean velocity data, False to use the latest single time data
# It is recommended to set to False for large areas and small step sizes because
# retrieving data from the HYCOM dataset is the most time-consuming part.
# Using single time data can significantly decrease retrieval time.
IS_MEAN = True

ROOT_URL = 'https://tds.hycom.org/thredds/dodsC/GLBy0.08/latest'


def str2bool(val):
    """
    Author:     xiao.qi@tamu.edu
    Created:    2024-07-09
    Modified:   2024-07-09
    Notes:      A util function to convert string to bool.
    """
    if isinstance(val, bool):
        return val
    if val.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    if val.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    raise argparse.ArgumentTypeError('Boolean value expected.')


def get_hycom_args():
    """
    Author:     xiao.qi@tamu.edu
    Created:    2024-07-05
    Modified:   2024-07-09
    Notes:      Gets command line args.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-la0', '--lat_start', type=int, default=LAT_START)
    parser.add_argument('-la1', '--lat_end', type=int, default=LAT_END)
    parser.add_argument('-lo0', '--lon_start', type=int, default=LON_START)
    parser.add_argument('-lo1', '--lon_end', type=int, default=LON_END)
    parser.add_argument('-s', '--step_size', type=int, default=STEP_SIZE)
    parser.add_argument('-m', '--is_mean', type=str2bool, default=IS_MEAN)

    args = vars(parser.parse_args())
    return args


def convert_hycom_time(time_lst, time_unit, is_mean):
    """
    Author:     xiao.qi@tamu.edu
    Created:    2024-07-09
    Modified:   2024-07-09
    Notes:      Convert and filter hycom time list to today's time range
    """
    time_now = datetime.utcnow()
    today = datetime(time_now.year, time_now.month, time_now.day)
    tomorrow = today + timedelta(days=1)

    time_hycom_list = num2date(time_lst, time_unit)

    if is_mean:
        condition = (time_hycom_list >= today) & (time_hycom_list <= tomorrow)
        time_hycom_today, = np.where(condition)
        # Calculate the mean time of all forecasts for today
        ref_time = num2date(np.mean(time_lst[time_hycom_today]), time_unit)
        time_range = f'{time_hycom_today[0]}:1:{time_hycom_today[-1] + 1}'
    else:
        time_hycom_today, = np.where(time_hycom_list <= time_now)
        ref_time = num2date(time_lst[time_hycom_today[-1]], time_unit)
        time_range = f'{time_hycom_today[-1]}'

    ref_time = ref_time.strftime('%Y-%m-%d %H:%M:%S')
    ref_string = 'daily average' if is_mean else 'single time'
    logging.info(f'Using the latest {ref_string} data.')
    logging.info(f'The time of the forecast is {ref_time} UTC.\n')

    return ref_time, time_range


def get_coords_time(lat_range, lon_range, is_mean):
    """
    Author:     xiao.qi@tamu.edu
    Created:    2024-07-05
    Modified:   2024-07-09
    Notes:      Gets hycom lat and lon list from the input range.
                Gets today's hycom time range info and converts it
                to a human-readable format.
    """
    fid = f'{ROOT_URL}?lat[{lat_range}],lon[{lon_range}],time[0:1:100]'
    dataset = Dataset(fid)
    lons = dataset.variables['lon'][:]
    lats = dataset.variables['lat'][:]
    time_lst = dataset.variables['time'][:]
    time_unit = dataset.variables['time'].units
    dataset.close()

    # Convert longitudes from 0 to 360 degree range to -180 to 180 degree range.
    lons[lons > 180] = lons[lons > 180] - 360
    logging.info('The forecast area is a rectangle bounded by:')
    logging.info(f'Latitude: {lats.min():.1f} to {lats.max():.1f}')
    logging.info(f'longitude: {lons.min():.1f} to {lons.max():.1f}\n')

    ref_time, time_range = convert_hycom_time(time_lst, time_unit, is_mean)

    return lats, lons, ref_time, time_range


def get_velocity(direction, time_range, lat_range, lon_range, is_mean):
    """
    Author:     xiao.qi@tamu.edu
    Created:    2024-07-05
    Modified:   2024-07-09
    Notes:      Retrieves hycom velocity data and converts it for
                Leaflet-velocity usage.
    """
    fid = f'{ROOT_URL}?{direction}[{time_range}][0][{lat_range}][{lon_range}]'
    dataset = Dataset(fid)
    velocity = dataset.variables[direction][:]
    dataset.close()

    if is_mean:
        # Get the daily average by taking the mean along the time axis
        velocity = np.nanmean(velocity, axis=0)
    velocity = np.squeeze(velocity)  # Remove singleton depth and time dimension
    velocity[np.isnan(velocity)] = 0
    velocity = velocity[::-1]
    velocity = velocity.flatten().tolist()
    return velocity


def write_to_file(coords_change_per_step, lats, lons, ref_time, data_lst):
    """
    Author:     xiao.qi@tamu.edu
    Created:    2024-07-05
    Modified:   2024-07-11
    Notes:      Uses a template file to format and write data to a JSON file.
    """
    # 2024-07-11 rdc added template and streamlines file defs
    template_file = '/data/gandalf/templates/wind-global.sample.json'
    streamlines_file = '/data/gandalf/hycom/hycom_surface_current_v2.json'

    with open(template_file, 'r', encoding='utf-8') as template_file:
        json_template = json.loads(template_file.read())

    # i = 0, eastward-current; i = 1, northward-current
    for i in range(2):
        json_template[i]['header']['dx'] = coords_change_per_step['lon']
        json_template[i]['header']['dy'] = coords_change_per_step['lat']
        json_template[i]['header']['la1'] = lats[-1]
        json_template[i]['header']['la2'] = lats[0]
        json_template[i]['header']['lo1'] = lons[0]
        json_template[i]['header']['lo2'] = lons[-1]
        json_template[i]['header']['nx'] = len(lons)
        json_template[i]['header']['ny'] = len(lats)
        json_template[i]['header']['refTime'] = ref_time
        json_template[i]['data'] = data_lst[i]

    with open(streamlines_file, 'w', encoding='utf-8') as f_out:
        json.dump(json_template, f_out)


def hycom_streamlines():
    """
    Author:     xiao.qi@tamu.edu
    Created:    2024-07-05
    Modified:   2024-07-09
    Notes:      Main entry point. Sets up lat and long range and horizontal
                resolution, retrieves the current velocity HYCOM data for this
                area, converts it for Leaflet-velocity usage, and saves it to
                a JSON file.
    """
    args = get_hycom_args()

    step_size = args['step_size']
    is_mean = args['is_mean']

    coords_change_per_step = {
        'lat': 0.04 * step_size,
        'lon': 0.08 * step_size,
    }

    lat_range = f'{args["lat_start"]}:{step_size}:{args["lat_end"]}'
    lon_range = f'{args["lon_start"]}:{step_size}:{args["lon_end"]}'

    lats, lons, ref_time, time_range = get_coords_time(lat_range, lon_range, is_mean)

    data_lst = []
    for direction in ['water_u', 'water_v']:
        logging.info(f'harvesting and calculating velocity for {direction}')

        data = get_velocity(direction, time_range, lat_range, lon_range, is_mean)
        data_lst.append(data)

    write_to_file(coords_change_per_step, lats, lons, ref_time, data_lst)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_time = time.time()
    hycom_streamlines()
    end_time = time.time()
    minutes = (end_time - start_time) / 60
    logging.warning('Duration: %0.2f minutes' % minutes)
