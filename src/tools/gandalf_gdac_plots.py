#!/usr/bin/env python3
"""
Creates plots in 'OG' style using csv and pandas

Name:       gandalf_gdac_plots.py
Author:     bob.currier@gcoos.org
Created:    2018-10-10
Modified:   2022-06-14
            Rewrote to work with CICESE SeaGliders. Now adding standard
            SG BaseStation data pipeline capacity. Both CICESE and Standard
            work using sensors.csv so there should be very few changes. The
            biggest change will be adding vector plots for depth_avg_curr --
            not sure if we will have that data in CICESE files. Also need
            to build a vehicle dashboard for non-science sensors.
            2022-06-24: Duplicated gandalf_sg_plots to gandalf_gdac_plots.
            We now have gandalf_process_gdac generating sensors.csv files
            so we can use almost all of this code as it. I removed the
            depth averaged currents function as Slocums don't provide.

            This code uses several changes from the standard plotting. We use
            'gdac_sensor' vs 'sensor' (in the sensors.json file) and we have
            to deal with time being in string vs epoch as comes from slocum.
"""
import sys
import time
import gc
import json
import time
import logging
import math
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import cmocean
from datetime import datetime
from matplotlib import dates as mpd
from matplotlib import pyplot as plt
from matplotlib import colors as colors
from matplotlib import cm as cm
from gandalf_utils import get_vehicle_config, get_sensor_config, flight_status
from gandalf_slocum_local import dinkum_convert
from geojson import Feature, Point, FeatureCollection, LineString

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



def get_sensor_plot_range(vehicle, sensor):
    """
    Gets plot range for each sensor so we don't overshoot."""
    logging.info("get_sensor_plot_range(%s, %s)" % (vehicle, sensor))
    sensors = get_sensor_config(vehicle)
    for record in sensors:
        if record['gdac_sensor'] == sensor:
            sensor_plot_min = float(record['sensor_plot_min'])
            sensor_plot_max = float(record['sensor_plot_max'])
            return (sensor_plot_min, sensor_plot_max)



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
    sensor_min = np.nanmin(data_frame[sensor])
    sensor_max = np.nanmax(data_frame[sensor])
    logging.info('normalize_sensor_range(): %s, %s, %s, %s' % (sensor, vehicle,
                 sensor_min, sensor_max))
    sensor_plot_min, sensor_plot_max = get_sensor_plot_range(vehicle, sensor)
    logging.debug("normalize_sensor_range(%s): %0.4f min, %0.4f max readings" %
          (sensor, sensor_min, sensor_max))
    if sensor_min < sensor_plot_min:
        logging.debug ("normalize_sensor_range(%s): adjusting min %0.4f to %0.4f" %
               (sensor, sensor_min, sensor_plot_min))
        sensor_min = float(sensor_plot_min)
    if sensor_max > sensor_plot_max:
        logging.debug ("normalize_sensor_range(%s): adjusting max %0.4f to %0.4f" %
               (sensor, sensor_max, sensor_plot_max))
        sensor_max = float(sensor_plot_max)
    logging.info("normalize_sensor_range(%s): Plotting with %0.4f MIN and %0.4f MAX" %
          (sensor, sensor_min, sensor_max))
    return(sensor_min, sensor_max)


def gdac_plot_sensor(config, vehicle, sensor):
    """
    Name:       gdac_plot_sensor
    Author:     robertdcurrier@gmail.com
    Created:    2018-11-06
    Modified:   2022-06-14
    Notes:      Really need to refactor and clean.
                Far too long for single function.
    """
    logging.info('gdac_plot_sensor(%s): %s' % (vehicle, sensor))
    fig = config_date_axis(config, vehicle)
    status = flight_status(vehicle)

    # Get config settings
    sensors = get_sensor_config(vehicle)
    alt_colormap = config['gandalf']['plots']['alt_colormap']
    if alt_colormap:
        for index, value in enumerate(sensors):
            if value["gdac_sensor"] == sensor:
                cmap = value["alt_colormap"]
    else:
        cmap = 'jet'

    logging.info("plot_sensor(): using %s colormap for %s" % (cmap, sensor))
    for index, value in enumerate(sensors):
            if value["gdac_sensor"] == sensor:
                log_scale = bool(value["log_scale"])
                logging.debug("plot_sensor(%s): Log scale is %s" % (sensor,
                                                                    log_scale))
    if status == 'deployed':
        data_dir = config['gandalf']['deployed_data_dir']
    if status == 'recovered':
        data_dir = config['gandalf']['post_data_dir_root']
    file_name = "%s/processed_data/sensors.csv" % (data_dir)

    logging.debug('make_plots(): Config file %s' % file_name)
    try:
        data_frame = pd.read_csv(file_name)
    except FileNotFoundError as e:
        logging.warning('gandalf_slocum_plots(%s): %s' % (vehicle, e))
        sys.exit()

    df_len = (len(data_frame))
    if df_len == 0:
        logging.debug('gandalf_slocum_plots(): Empty Data Frame')
        return
    data_frame['depth'] = (data_frame['depth'].interpolate(method='pad'))
    data_frame['temperature'] = (data_frame['temperature'].interpolate(method='pad'))
    data_frame['salinity'] = (data_frame['salinity'].interpolate(method='pad'))

    # Start and End date/time
    start_date = (time.strftime("%Y-%m-%d",
                  time.strptime(config["trajectory_datetime"],
                                "%Y%m%dT%H%M%S")))
    end_date = (datetime.strptime(data_frame['time'].iloc[-1],
                     '%Y-%m-%dT%H:%M:%SZ'))
    end_date = end_date.strftime("%Y-%m-%d")

    logging.info("plot_sensor(): plotting %s" % sensor)
    logging.info("plot_sensor(): start_date %s" % start_date)
    logging.info("plot_sensor(): end_date %s" % end_date)
    # Title and subtitle
    for record in sensors:
        if (record['gdac_sensor'] == sensor):
            subtitle_string = "%s %s" % (record['sensor_name'],
                                         record['unit_string'])
            break

    title_string = "%s %s to %s\n %s" % (config['gandalf']['public_name'],
                                         start_date, end_date, subtitle_string)
    plt.title(title_string, fontsize=12, horizontalalignment='center')

    # rudimentary bounds checking
    data_frame = data_frame[data_frame['temperature'] != 0]
    data_frame = data_frame[data_frame['depth'] > 0]

    # Set plot ranges to account for over/under spikes
    (sensor_min, sensor_max) = normalize_sensor_range(sensor, vehicle,
                                                      data_frame)

    plt.gca().invert_yaxis()

    # SCATTER IT
    # check for alt_colormaps
    if config['gandalf']['plots']['alt_colormap']:
        logging.debug('Using alt_colormap...')
    max_depth = max(data_frame['depth'])

    plt.ylim(max_depth + config['gandalf']['plots']['plot_depth_padding'])

    plt.scatter(mpd.epoch2num(data_frame.epoch),
                data_frame['depth'], s=15,
                c=data_frame[sensor],
                lw=0, marker='8', cmap=cmap)
    if status == 'deployed':
        plot_dir = config['gandalf']['plots']['deployed_plot_dir']
    else:
        plot_dir = config['gandalf']['plots']['postprocess_plot_dir']
    plt.colorbar().set_label(config.get(
                             sensor, record['unit_string']), fontsize=10)
    plt.clim(sensor_min, sensor_max)

    add_logo(vehicle, fig)


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


def add_logo(vehicle,fig):
    """Add insitutional logo to plot

    Name:       add_logo
    Author:     robertdcurrier@gmail.com
    Created:    2018-11-06
    Modified:   2022-06-13
    Notes:
    """
    config = get_vehicle_config(vehicle)
    logging.info('add_logo(%s)' % vehicle)
    logo_file = config['gandalf']['plots']['logo_file']
    logging.debug('plot_sensor(): Using %s for logo file' % logo_file)
    the_logo = plt.imread(logo_file)
    logo_loc = config['gandalf']['plots']['logo_loc']
    plt.figimage(the_logo, logo_loc[0], logo_loc[1], zorder=10)


def gandalf_gdac_plots(vehicle):
    """Entry point

    Name:       gandalf_gdac_plots
    Author:     robertdcurrier@gmail.com
    Created:    2018-11-06
    Modified:   2022-06-14
    Notes:
    """
    logging.info('gandalf_gdac_plots(%s)' % vehicle)
    config = get_vehicle_config(vehicle)
    plot_sensor_list = config['gandalf']['plots']['plot_sensor_list']
    for sensor in plot_sensor_list:
        gdac_plot_sensor(config, vehicle, sensor)


def get_cli_args():
    """What it say.

    Name:       get_cli_args
    Author:     robertdcurrier@gmail.com
    Created:    2018-11-06
    Modified:   2021-05-16
    """
    logging.info('get_cli_args()')
    arg_p = argparse.ArgumentParser()
    arg_p.add_argument("-v", "--vehicle", help="vehicle name",
                       nargs="?", required='True')
    args = vars(arg_p.parse_args())
    return args


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start = time.time()
    args = get_cli_args()
    vehicle = args['vehicle']
    register_cmocean()
    gandalf_gdac_plots(vehicle)
    end = time.time()
    ttime = end - start
    logging.info('gandalf_gdac_plots(): Run time was %s' % ttime)
