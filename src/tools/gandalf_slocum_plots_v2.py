#!/usr/bin/env python3
"""
Creates plots in 'OG' style using csv and pandas vs
PostGreSQL table

Name:       gandalf_slocum_plots_v2
Author:     bob.currier@gcoos.org
Created:    2018-10-10
Modified:   2022-10-17
            Changed logging.debug() to logging.debug/info and dropped
            all print() statements
            Went with argparse
"""
import sys
import time
import gc
import json
import time
import math
import logging
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import cmocean
import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime
from matplotlib import dates as mpd
from matplotlib import pyplot as plt
from matplotlib import colors as colors
from matplotlib import cm as cm
from gandalf_utils import get_vehicle_config, get_sensor_config
from gandalf_utils import flight_status
from gandalf_slocum_local import dinkum_convert
from geojson import Feature, Point, FeatureCollection, LineString
import statsmodels.api as sm_api
import warnings
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.WARNING)

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


def add_logo(vehicle,fig):
    """
    Cleaning up plot_sensor and refactoring. Herein lies the logo part
    """
    config = get_vehicle_config(vehicle)
    logging.info('add_logo(%s)' % vehicle)
    logo_file = config['gandalf']['plots']['logo_file']
    logging.debug('plot_sensor(): Using %s for logo file' % logo_file)
    the_logo = plt.imread(logo_file)
    logo_loc = config['gandalf']['plots']['logo_loc']
    plt.figimage(the_logo, logo_loc[0], logo_loc[1], zorder=10)


def get_sensor_plot_range(vehicle, sensor):
    """
    Gets plot range for each sensor so we don't overshoot."""
    logging.info("get_sensor_plot_range(%s, %s)" % (vehicle, sensor))
    sensors = get_sensor_config(vehicle)
    for record in sensors:
        if record['sensor'] == sensor:
            sensor_plot_min = float(record['sensor_plot_min'])
            sensor_plot_max = float(record['sensor_plot_max'])
            return (sensor_plot_min, sensor_plot_max)


def register_cmocean():
    """Does what it says."""
    matplotlib.colormaps.register(name='thermal', cmap=cmocean.cm.thermal)
    matplotlib.colormaps.register(name='haline', cmap=cmocean.cm.haline)
    matplotlib.colormaps.register(name='algae', cmap=cmocean.cm.algae)
    matplotlib.colormaps.register(name='matter', cmap=cmocean.cm.matter)
    matplotlib.colormaps.register(name='dense', cmap=cmocean.cm.dense)
    matplotlib.colormaps.register(name='oxygen', cmap=cmocean.cm.oxy)
    matplotlib.colormaps.register(name='speed', cmap=cmocean.cm.speed)
    matplotlib.colormaps.register(name='turbid', cmap=cmocean.cm.turbid)
    matplotlib.colormaps.register(name='tempo', cmap=cmocean.cm.turbid)


def config_date_axis(config, vehicle):
    """
    Sets up our style
    """
    logging.debug("config_date_axis(): Setting x axis for date/time display")
    # instantiate the plot
    fig = plt.figure(figsize=(14, 6))
    gca = plt.gca()
    # make room for xlabel
    plt.subplots_adjust(bottom=0.15)
    # labels
    plt.ylabel('Depth (m)')
    # ticks
    """
    Sets up date/time x axis
    Modified: 2020-05-19
    """
    gca.xaxis.set_tick_params(which='major')
    plt.setp(gca.xaxis.get_majorticklabels(), rotation=45, fontsize=6)
    major_formatter = mpd.DateFormatter('%m/%d')
    gca.xaxis.set_major_formatter(major_formatter)
    gca.set_xlabel('Date', fontsize=12)

    return (fig)


def normalize_sensor_range(sensor, vehicle, data_frame):
    """ Set sane sensor ranges."""
    sensor_min = np.nanmin(data_frame[sensor])
    sensor_max = np.nanmax(data_frame[sensor])
    sensor_plot_min, sensor_plot_max = get_sensor_plot_range(vehicle, sensor)
    logging.info("normalize_sensor_range(%s): %0.4f min, %0.4f max readings" %
          (sensor, sensor_min, sensor_max))
    if sensor_min < sensor_plot_min:
        logging.info ("normalize_sensor_range(%s): adjusting min %0.4f to %0.4f" %
               (sensor, sensor_min, sensor_plot_min))
        sensor_min = float(sensor_plot_min)

    if sensor_max > sensor_plot_max:
        logging.info ("normalize_sensor_range(%s): adjusting max %0.4f to %0.4f" %
               (sensor, sensor_max, sensor_plot_max))
        sensor_max = float(sensor_plot_max)
    logging.info("normalize_sensor_range(%s): Plotting with %0.4f MIN and %0.4f MAX" %
          (sensor, sensor_min, sensor_max))
    return(sensor_min, sensor_max)


def interpolate_linear(x, indices, x_array, y_array):
    """
    Author:     xiao.qi@tamu.edu
    Created:    2024-07-12
    Modified:   2024-07-12
    Notes:      This function performs linear interpolation on given arrays
                based on specified indices. It calculates the interpolated
                values of 'y' corresponding to the input 'x' using the values
                from 'x_array' and 'y_array'.

                The interpolation is based on the formula:
                y = y0 + (x - x0) * (y1 - y0) / (x1 - x0)

                Parameters:
                x : float
                    The value at which to interpolate.
                indices : array-like
                    The indices of the points in 'x_array' that bracket the  'x0'
                x_array : pandas Series or numpy array
                    The array of x values.
                y_array : pandas Series or numpy array
                    The array of y values.

                Returns:
                y : numpy array
                    The interpolated y values corresponding to the input 'x'
    """
    x0 = x_array.iloc[indices].values
    x1 = x_array.iloc[indices + 1].values

    y0 = y_array.iloc[indices].values
    y1 = y_array.iloc[indices + 1].values

    y = y0 + (x - x0) * (y1 - y0) / (x1 - x0)
    return y


def plot_26C_line(df):
    """
    Author:     xiao.qi@tamu.edu
    Created:    2024-07-10
    Modified:   2024-07-12
    Notes:      The function plots the 26°C isotherm line from a given DataFrame
                containing water temperature and depth data. The function
                performs the following steps:

                1. Filters out rows with missing 'sci_m_present_time' values
                   and resets the DataFrame index.
                2. Identifies the points where the water temperature crosses
                   the 26°C threshold.
                3. Interpolates the 'sci_m_present_time' and 'm_depth' values
                   at the threshold crossings.
                4. Applies LOESS (Local Regression) to fit a smooth curve.
                5. Plots the smoothed 26°C line.

    Parameters: df : pandas DataFrame
                    The input DataFrame containing the columns 'sci_water_temp',
                    'sci_m_present_time', and 'm_depth'.
    """
    threshold = 26
    df = df.dropna(subset=['sci_m_present_time', 'sci_water_temp', 'm_depth'])
    df = df.reset_index(drop=True)  # Convenient to interpolate

    if df['sci_m_present_time'].is_monotonic_increasing is not True:
        logging.error("The time should be monotonic increasing.")
        return

    temp_array = df['sci_water_temp']
    condition = (
            (temp_array < threshold) & (temp_array.shift(-1) > threshold) |
            (temp_array > threshold) & (temp_array.shift(-1) < threshold)
    )
    indices = df[condition].index
    indices = indices[1:-1]  # Trim to avoid insufficient data points at edge

    times = interpolate_linear(threshold, indices, temp_array, df['sci_m_present_time'])
    times = mpd.epoch2num(times)

    depths = interpolate_linear(threshold, indices, temp_array, df['m_depth'])

    # frac specifies the fraction of the data used when estimating each y-value
    # Smaller value: less smoothing; Larger value: more smoothing
    lowess = sm_api.nonparametric.lowess
    y_smooth = lowess(depths, times, frac=0.05)

    # Plot smooth line
    plt.plot(y_smooth[:, 0], y_smooth[:, 1], color='black')


def plot_sensor(config, vehicle, sensor):
    """
    Gets jiggy wit it
    """
    logging.info('plot_sensor(%s): %s' % (vehicle, sensor))
    fig = config_date_axis(config, vehicle)
    status = flight_status(vehicle)

    # Get config settings
    sensors = get_sensor_config(vehicle)
    alt_colormap = config['gandalf']['plots']['alt_colormap']
    if alt_colormap:
        for index, value in enumerate(sensors):
            if value["sensor"] == sensor:
                cmap = value["alt_colormap"]
    else:
        cmap = 'jet'
    logging.info('plot_sensor(): Processing %s' % sensor)
    logging.info("plot_sensor(): using %s colormap for %s" % (cmap, sensor))
    for index, value in enumerate(sensors):
            if value["sensor"] == sensor:
                log_scale = bool(value["log_scale"])
                logging.debug("plot_sensor(%s): Log scale is %s" % (sensor, log_scale))

    if status == 'deployed':
        data_dir = config['gandalf']['deployed_data_dir']
    if status == 'recovered':
        data_dir = config['gandalf']['post_data_dir_root']

    # read CSV -- UPDATE NOW USING COMMAND LINE OPTION
    if len(sys.argv) == 4:
        file_name = sys.argv[2]
        logging.debug('make_plots(): Command line file %s' % file_name)
    else:
        file_name = "%s/processed_data/sensors.csv" % (data_dir)
        logging.debug('make_plots(): Config file %s' % file_name)
    data_frame = pd.read_csv(file_name)

    df_len = (len(data_frame))
    if df_len == 0:
        logging.debug('gandalf_slocum_plots(): Empty Data Frame')
        return

    # Start and End date/time
    start_date = (time.strftime("%Y-%m-%d",
                  time.strptime(config["trajectory_datetime"],
                                "%Y%m%dT%H%M")))
    end_date = datetime.fromtimestamp(
        np.nanmax(data_frame['m_present_time']))
    end_date = end_date.strftime("%Y-%m-%d")

    logging.info("plot_sensor(): plotting %s" % sensor)
    logging.info("plot_sensor(): start_date %s" % start_date)
    logging.info("plot_sensor(): end_date %s" % end_date)
    # Title and subtitle
    for record in sensors:
        if (record['sensor'] == sensor):
            log_scale = bool(record['log_scale'])
            if log_scale:
                subtitle_string = "%s %s Log Scale" % (record['sensor_name'],
                                                       record['unit_string'])
                break
            else:
                subtitle_string = "%s %s" % (record['sensor_name'],
                                             record['unit_string'])
                break

    title_string = "%s %s to %s\n %s" % (config['gandalf']['public_name'],
                                         start_date, end_date, subtitle_string)
    plt.title(title_string, fontsize=12, horizontalalignment='center')

    # Interpolate the NaNs of sci_water_pressure so we can get depths for all
    data_frame['sci_water_pressure'] = (
                                        data_frame['sci_water_pressure'].
                                        interpolate(method='pad'))
    data_frame['m_depth'] = (data_frame['m_depth'].interpolate(method='pad'))
    # rudimentary bounds checking
    data_frame = data_frame[data_frame['sci_water_temp'] != 0]
    data_frame = data_frame[data_frame['m_depth'] > 0]
    data_frame = data_frame[data_frame['sci_water_cond'] != 0]

    # Set plot ranges to account for over/under spikes
    (sensor_min, sensor_max) = normalize_sensor_range(sensor, vehicle,
                                                      data_frame)

    use_bottom = (config['gandalf']['plots']['use_bottom'])

    plt.gca().invert_yaxis()
    # 2019-08-20 added this as mote-genie was ripping out way
    # out-of-band m_depth numbers
    if config['gandalf']['plots']['use_max_plot_depth']:
        logging.debug("gandalf_slocum_plots(): Using max_plot_depth")
        max_plot_depth = config['gandalf']['plots']['max_plot_depth']
    else:
        max_plot_depth = (np.nanmax(data_frame['m_depth'] +
                          config['gandalf']['plots']['plot_depth_padding']))
    # invert it
    if(np.nanmax(data_frame['m_depth']) > max_plot_depth):
        logging.debug('DATA FRAME MAX DEPTH IS %0.2f' %  np.nanmax(data_frame['m_depth']))
    plt.ylim(max_plot_depth)

    # SCATTER IT
    # check for alt_colormaps
    if config['gandalf']['plots']['alt_colormap']:
        logging.debug('Using alt_colormap...')

        plt.scatter(mpd.epoch2num(data_frame.sci_m_present_time),
                    data_frame['sci_water_pressure'] * 10, s=15,
                    c=data_frame[sensor],
                    lw=0, marker='8', cmap=cmap)

        plt.colorbar().set_label(config.get(
                                 sensor, record['unit_string']),
                                 fontsize=10)
        plt.clim(sensor_min, sensor_max)

    # bottoms up
    if use_bottom:
        logging.debug("Using bottom...")
        logging.debug("Interpolating m_water_depth...")

        data_frame['m_water_depth'] = (data_frame['m_water_depth'].
                                       interpolate(method='pad'))

        plt.scatter(mpd.epoch2num(data_frame.sci_m_present_time),
                    data_frame.m_water_depth, marker='.', c='k', s=1, lw=0)

    add_logo(vehicle, fig)
    # 26C line
    if sensor == 'sci_water_temp' and config['gandalf']['plots']['use_26d']:
        logging.info("Start plotting the 26C degree line")
        plot_26C_line(data_frame)

    # save it
    if status == 'deployed':
        plot_dir = config['gandalf']['plots']['deployed_plot_dir']
    else:
        plot_dir = config['gandalf']['plots']['postprocess_plot_dir']

    # UPDATE CHECK for sensor_file command line arg and if true write local
    if len(sys.argv) == 4:
            plot_file = "/data/gandalf/tmp/%s.png" % (sensor)
    else:
        # Use config file settings
        plot_file = "%s/%s.png" % (plot_dir, sensor)
    logging.info("plot_sensor(): Writing %s" % (plot_file))
    plt.savefig(plot_file, dpi=100)
    # close figure
    plt.close(fig)
    logging.debug("plot_sensor(): Collecting garbage...")
    gc.collect()
    logging.debug("-----------------------------------------------------")


def make_plots(vehicle):
    """
    The boss
    """
    config = get_vehicle_config(vehicle)
    plot_sensor_list = config['gandalf']['plots']['plot_sensor_list']
    # Okay here we go with multiprocessing
    for sensor in plot_sensor_list:
        if sensor == 'depth_avg_curr':
            plot_dac(vehicle)
            continue
        else:
            (plot_sensor(config, vehicle, sensor))


def plot_dac(vehicle):
    """
    Name:       plot_dac
    Author:     bob.currier@gcoos.org
    Created:    2022-05-19
    Modified:   2022-10-17
    Notes:      Created to plot depth_avg_curr for Slocums using
                m_water_vy and m_water_vy. Slocums quite different from
                Seagliders so we had to substantially mod the code.
    """
    logging.info('plot_dac(%s)', vehicle)
    status = flight_status(vehicle)
    config = get_vehicle_config(vehicle)
    fig = plt.figure(figsize=(12, 6))
    gca = plt.gca()


    if status == 'deployed':
        data_dir = config['gandalf']['deployed_data_dir']
        plot_dir = config['gandalf']['plots']['deployed_plot_dir']
    if status == 'recovered':
        data_dir = config['gandalf']['post_data_dir_root']
        plot_dir = config['gandalf']['plots']['postprocess_plot_dir']

    file_name = "%s/processed_data/sensors.csv" % (data_dir)
    logging.debug('plot_dac(): Config file %s' % file_name)
    vector_frame = pd.read_csv(file_name)
    vector_frame = vector_frame.dropna(subset=['m_water_vy'])
    vector_frame = vector_frame.dropna(subset=['m_water_vy'])

    u = vector_frame.m_water_vx
    v = vector_frame.m_water_vy
    timestamps = vector_frame['m_present_time']

    # Start and End date/time
    start_date = (time.strftime("%Y-%m-%d",
                  time.strptime(config["trajectory_datetime"],
                                "%Y%m%dT%H%M")))
    end_date = datetime.fromtimestamp(np.nanmax(timestamps))
    end_date = end_date.strftime("%Y-%m-%d")
    sensor = 'Depth Averaged Currents'
    logging.info("plot_dac(): plotting %s" % sensor)
    logging.info("plot_dac(): start_date %s" % start_date)
    logging.info("plot_dac(): end_date %s" % end_date)
    subtitle_string = sensor
    title_string = "%s %s to %s\n %s" % (config['gandalf']['public_name'],
                                         start_date, end_date, subtitle_string)
    plt.title(title_string, fontsize=12, horizontalalignment='center')
    add_logo(vehicle, fig)
    plt.xlabel('Date')
    plt.ylabel('Velocity (m/s)')
    plt.tick_params(axis='x',
                    bottom=False,
                    labelbottom=False)

    plt.quiver(u, v, color='blue')
    plot_file = "%s/%s.png" % (plot_dir, "depth_avg_curr")
    logging.info("plot_dac(): Writing %s" % (plot_file))
    plt.savefig(plot_file, dpi=100)

if __name__ == '__main__':
    register_cmocean()
    args = get_cli_args()
    vehicle = args['vehicle']
    make_plots(vehicle)
