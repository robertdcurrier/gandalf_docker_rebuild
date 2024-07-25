#!/usr/bin/env python3
"""
Create line plots for Saildrone data

Name:       gandalf_sd_plots
Author:     bob.currier@gcoos.org
Created:    2022-09-22
Modified:   2022-09-22
"""
import sys
import time
import gc
import json
import time
import logging
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
from datetime import datetime
from matplotlib import dates as mpd
from matplotlib import pyplot as plt
from matplotlib import colors as colors
from matplotlib import cm as cm
from gandalf_utils import get_vehicle_config, get_sensor_config
from gandalf_utils import flight_status
from gandalf_slocum_local import dinkum_convert
from geojson import Feature, Point, FeatureCollection, LineString
import warnings
warnings.filterwarnings("ignore")


def get_sensor_plot_range(vehicle, sensor):
    """
    Gets plot range for each sensor so we don't overshoot."""
    logging.debug("get_sensor_plot_range(%s, %s)" % (vehicle, sensor))
    sensors = get_sensor_config(vehicle)
    for record in sensors:
        if record['sensor'] == sensor:
            sensor_plot_min = float(record['sensor_plot_min'])
            sensor_plot_max = float(record['sensor_plot_max'])
            return (sensor_plot_min, sensor_plot_max)


def config_date_axis(config, vehicle, subtitle_string):
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
    plt.ylabel(subtitle_string)
    # ticks
    """
    Sets up date/time x axis
    Modified: 2020-05-19
    """
    # hours = mpd.HourLocator(interval = 6)
    gca.xaxis.set_tick_params(which='major')
    plt.setp(gca.xaxis.get_majorticklabels(), rotation=45, fontsize=6)
    major_formatter = mpd.DateFormatter('%m/%d')
    # gca.xaxis.set_major_locator(hours)
    gca.xaxis.set_major_formatter(major_formatter)
    gca.set_xlabel('Date', fontsize=12)

    return fig


def normalize_sensor_range(sensor, vehicle, data_frame):
    """ Set sane sensor ranges."""
    logging.debug('normalize_sensor_range(%s) for %s', vehicle, sensor)
    sensor_min = np.nanmin(data_frame[sensor])
    sensor_max = np.nanmax(data_frame[sensor])

    # GOTTA CHANGE SENSOR NAMES IN SENSOR FILE -- NO SD SENSORS IN DERE MON
    sensor_plot_min, sensor_plot_max = get_sensor_plot_range(vehicle, sensor)

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


def sd_plot_sensor(config, vehicle, sensor):
    """
    Author:     bob.currier@gcoos.org
    Created:    2022-09-22
    Modified:   2022-09-22
    Notes:      Gets jiggy wit it
    """
    status = flight_status(vehicle)

    # Get config settings
    sensors = get_sensor_config(vehicle)


    if status == 'deployed':
        data_dir = config['gandalf']['deployed_data_dir']
        file_name = config['gandalf']['deployed_sensors_csv']
    if status == 'recovered':
        file_name = config['gandalf']['post_sensors_csv']
        data_dir = config['gandalf']['post_data_dir_root']

    try:
        data_frame = pd.read_csv(file_name)
    except IOError as e:
        logging.warning('sd_plot_sensor(%s): Could not read CSV.', vehicle)
        return

    df_len = (len(data_frame))
    if df_len == 0:
        logging.debug('gandalf_sd_plots(%s): Empty Data Frame.', vehicle)
        return

    # Start and End date/time
    start_date = (time.strftime("%Y-%m-%d",
                  time.strptime(config["trajectory_datetime"],
                                "%Y%m%dT%H%M")))
    end_date = datetime.fromtimestamp(
        np.nanmax(data_frame['epoch']))
    end_date = end_date.strftime("%Y-%m-%d")

    logging.info("sd_plot_sensor(): plotting %s" % sensor)
    logging.info("sd_plot_sensor(): start_date %s" % start_date)
    logging.info("sd_plot_sensor(): end_date %s" % end_date)

    # Title and subtitle
    for record in sensors:
        if (record['sensor'] == sensor):
            subtitle_string = "%s %s" % (record['sensor_name'],
                                         record['unit_string'])
            title_string = "%s %s to %s\n %s" % (config['gandalf']['public_name'],
                                                 start_date, end_date, subtitle_string)
    # Set plot ranges to account for over/under spikes
    (sensor_min, sensor_max) = normalize_sensor_range(sensor, vehicle,
                                                      data_frame)

    # add logo
    logo_file = config['gandalf']['plots']['logo_file']
    logging.debug('sd_plot_sensor(): Using %s for logo file' % logo_file)
    the_logo = plt.imread(logo_file)
    logo_loc = config['gandalf']['plots']['logo_loc']

    fig = config_date_axis(config, vehicle, subtitle_string)
    plt.title(title_string, fontsize=12, horizontalalignment='center')
    plt.figimage(the_logo, logo_loc[0], logo_loc[1], zorder=10)

    # save it
    if status == 'deployed':
        plot_dir = config['gandalf']['plots']['deployed_plot_dir']
    else:
        plot_dir = config['gandalf']['plots']['postprocess_plot_dir']

    # Use config file settings
    plot_file = "%s/%s.png" % (plot_dir, sensor)
    if sensor == 'WIND_SPEED_MEAN':
        logging.info('sd_plot_sensor(): Converting m/s to knots')
        data_frame[sensor] = data_frame[sensor]*1.94384
    plt.plot(mpd.epoch2num(data_frame['epoch']), data_frame[sensor])
    logging.info("sd_plot_sensor(): Writing %s" % (plot_file))
    plt.savefig(plot_file, dpi=100)
    # close figure
    plt.close(fig)
    logging.debug("sd_plot_sensor(): Collecting garbage...")
    gc.collect()
    logging.debug("-----------------------------------------------------")



def get_cli_args():
    """
    Author:     robertdcurrier@gmail.com
    Created:    2018-11-06
    Modified:   2022-09-22
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


def gandalf_sd_plots(vehicle):
    """
    The boss
    """
    config = get_vehicle_config(vehicle)
    sd_plot_sensor_list = config['gandalf']['plots']['plot_sensor_list']
    # Okay here we go with multiprocessing
    for sensor in sd_plot_sensor_list:
        (sd_plot_sensor(config, vehicle, sensor))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    args = get_cli_args()
    vehicle = args["vehicle"]
    start = time.time()
    gandalf_sd_plots(vehicle)
    end = time.time()
    ttime = int(end - start)
    logging.info('gandalf_sd_plots(): Run time was %s seconds' % ttime)
