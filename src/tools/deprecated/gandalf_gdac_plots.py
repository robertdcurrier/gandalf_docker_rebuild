#!/usr/bin/env python3
import json
import os
import sys
import requests
import cmocean
import logging
import time
import pandas as pd
import numpy as np
import seawater as sw
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import dates as mpd
from datetime import datetime
from gandalf_utils import get_vehicle_config, get_sensor_config
from gandalf_utils import flight_status
matplotlib.use('Agg')
"""
Plots glider data obtained by ERDDAP from Glider DAC
"""

def get_erddap_data(vehicle):
    """
    Name:       get_erddap_data
    Author:     robertdcurrier@gmail.com
    Created:    2018-06-01
    Modified:   2022-06-09

    Notes:      We were fetching ERDDAP 3 times (track, plots, 3D) so we
    moved to one pull and write as text file for all further access
    """
    logging.info("get_erddap_data(%s)" % vehicle)
    config = get_vehicle_config(vehicle)
    json_dir = config["gandalf"]["gdac_json_dir"]
    json_file_name = ('%s/%s_gdac.json') % (json_dir, vehicle)
    # Need to check if file exists and bail if not
    logging.info('get_erddap_data(%s): Opening %s' % (vehicle, json_file_name))
    json_data = json.loads(open(json_file_name, 'r').read())
    return(json_data)


def build_df(vehicle, json_data):
    """
    Takes json data and extracts temp, salinity,
    density and sound velocity. Makes into a Pandas DF.
    Returns DF
    """
    logging.info("build_df(%s)" % vehicle)
    sensor_vals = []
    # for headers

    for feature in json_data['features']:
        time = (feature['properties']['time'])
        temp = (feature['properties']['temperature'])
        sal = (feature['properties']['salinity'])
        press = (feature['properties']['pressure'])
        density = (feature['properties']['density'])
        # Initially set sigma == density don't calc here as might be NaN
        sigma = density
        depth = (feature['properties']['depth'])
        # We do the calc here so need to ensure no blanks
        if (temp and sal and press is not None):
            svel = sw.svel(temp, sal, press)
        else:
            svel = None
        # We display sigma-t and density. Most erddap vehicles report density
        # so we must calc sigma-t.  Navy ng glider already report sigma-t so
        # thus this hack to convert back to density
        if density is not None:
            if density < 1000:
                # Navy reporting Sigma vs Density
                sigma = density
                density = (density+1000)
            else:
                sigma = (density - 1000)

        sensor_vals.append([time, depth, temp, sal, density, sigma, svel])
    # Create dataframe with headers
    df = pd.DataFrame(sensor_vals, columns=["m_present_time",
                                            "m_depth", "sci_water_temp",
                                            "calc_salinity", "calc_density",
                                            "calc_sigma", "calc_soundvel"])
    return(df)


def get_sensor_plot_range(vehicle, sensor):
    """
    Gets plot range for each sensor so we don't overshoot
    """
    logging.info("get_sensor_plot_range(%s): getting %s range" % (vehicle, sensor))
    sensors = get_sensor_config(vehicle)
    for record in sensors:
        if record['sensor'] == sensor:
            sensor_plot_min = record['sensor_plot_min']
            sensor_plot_max = record['sensor_plot_max']
            return sensor_plot_min, sensor_plot_max


def register_cmocean():
    """Does what it says."""
    logging.info("register_cmocean()")
    plt.register_cmap(name='thermal', cmap=cmocean.cm.thermal)
    plt.register_cmap(name='haline', cmap=cmocean.cm.haline)
    plt.register_cmap(name='algae', cmap=cmocean.cm.algae)
    plt.register_cmap(name='matter', cmap=cmocean.cm.matter)
    plt.register_cmap(name='dense', cmap=cmocean.cm.dense)
    plt.register_cmap(name='oxy', cmap=cmocean.cm.oxy)
    plt.register_cmap(name='speed', cmap=cmocean.cm.speed)


def config_plots(vehicle):
    """
    Sets up our style
    """
    # Get config settings
    logging.info("erddap_config_plots(): getting config")
    config = get_vehicle_config(vehicle)
    # instantiate the plot
    fig = plt.figure(figsize=(14, 6))
    gca = plt.gca()
    # make room for xlabel
    plt.subplots_adjust(bottom=0.15)
    # labels
    plt.ylabel('Depth (m)')
    # ticks
    """
    2019/02/22
    TO DO:
        Need to make date/time ticks auto-adjusting based on length
        of deployment. Right now it's all manual and takes far
        too much twiddling to get an acceptable setting for the plots.
    """
    # hours = mpd.HourLocator(interval = 12)
    gca.xaxis.set_tick_params(which='major')
    plt.setp(gca.xaxis.get_majorticklabels(), rotation=45, fontsize=6)
    major_formatter = mpd.DateFormatter('%m/%d')
    # gca.xaxis.set_major_locator(hours)
    gca.xaxis.set_major_formatter(major_formatter)
    gca.set_xlabel('Date', fontsize=12)

    return fig


def plot_sensor(vehicle, sensor, data_frame):
    """
    Gets jiggy wit it
    """
    fig = config_plots(vehicle)
    # Get config settings
    logging.debug("erddop_plot_sensor(%s): getting vehicle config" % vehicle)
    config = get_vehicle_config(vehicle)
    logging.debug("erddap_plot_sensor(%s): getting sensor config" % vehicle)
    sensors = get_sensor_config(vehicle)
    alt_colormap = bool(config['gandalf']['plots']['alt_colormap'])
    if alt_colormap:
        for index, value in enumerate(sensors):
            if value["sensor"] == sensor:
                cmap = value["alt_colormap"]
    else:
        cmap = 'jet'

    status = flight_status(vehicle)
    if status == 'deployed':
        data_dir = config['gandalf']['deployed_data_dir']
    if status == 'recovered':
        data_dir = config['gandalf']['post_data_dir_root']
    operator = config['gandalf']['operator']

    df_len = (len(data_frame))
    if df_len == 0:
        logging.warn('erddap_plot_sensor(%s): Empty Data Frame' % vehicle)
        return

    # Get Min/Max of sensor and data
    sensor_min = np.nanmin(data_frame[sensor])
    sensor_max = np.nanmax(data_frame[sensor])
    logging.debug("erddap_plot_sensor(): %s has %0.2f min, %02.f max" %
          (sensor, sensor_min, sensor_max))


    sensor_plot_min, sensor_plot_max = get_sensor_plot_range(vehicle, sensor)
    logging.info("erddap_plot_sensor(%s): Using %0.2f min, %0.2f max for %s" %
          (vehicle, sensor_plot_min, sensor_plot_max, sensor))

    if sensor_min < sensor_plot_min:
        sensor_min = sensor_plot_min
    if sensor_max > sensor_plot_max:
        logging.debug ("erddap_plot_sensor(%s): clipping max from %0.2f to %0.2f" %
               (sensor, sensor_max, sensor_plot_max))
        sensor_max = sensor_plot_max
    # Start and End date/time DIFFERENT FROM SLOCUM AS THESE COME IN
    # NON-EPOCH FORMAT
    # More than one way to hunt the wumpus. split() works just fine...
    start_date = np.nanmin(data_frame['m_present_time']).split('T')[0]
    end_date = np.nanmax(data_frame['m_present_time']).split('T')[0]

    logging.info("erddap_plot_sensor(%s): plotting %s" % (vehicle, sensor))
    logging.debug("erddap_plot_sensor(%s): start_date %s" % (vehicle,
                                                              start_date))
    logging.debug("erddap_plot_sensor(%s): end_date %s" % (vehicle, end_date))

    # Title and subtitle
    for record in sensors:
        if (record['sensor'] == sensor):
            subtitle_string = "%s %s" % (record['sensor_name'],
                                         record['unit_string'])
            break

    title_string = "%s %s to %s\n %s" % (config['gandalf']['public_name'],
                                         start_date, end_date, subtitle_string)
    plt.title(title_string, fontsize=12, horizontalalignment='center')

    # Interpolate the NaNs of sci_water_pressure so we can get depths for all
    data_frame['sci_water_temp'] = (data_frame['sci_water_temp'].interpolate())
    data_frame['calc_salinity'] = (data_frame['calc_salinity'].interpolate())
    data_frame['calc_density'] = (data_frame['calc_density'].interpolate())
    data_frame['m_depth'] = (data_frame['m_depth'].interpolate())

    # rudimentary bounds checking
    data_frame = data_frame[data_frame['sci_water_temp'] != 0]
    data_frame = data_frame[data_frame['m_depth'] > 0]

    plt.gca().invert_yaxis()
    logging.debug("Max Depth: %d" % np.nanmax(data_frame['m_depth']))
    # 2019-08-20 added this as mote-genie was ripping out way
    # out-of-band m_depth numbers
    use_max_plot_depth = bool(config['gandalf']['plots']['use_max_plot_depth'])
    if use_max_plot_depth:
        logging.info("erddap_plot_sensor(): Using max_plot_depth")
        max_plot_depth = config['gandalf']['plots']['max_plot_depth']
    else:
        max_plot_depth = np.nanmax(data_frame['m_depth'])
    logging.debug("erddap_plot_sensor(): Max Plot Depth: %d" %  max_plot_depth)
    # invert it
    plt.ylim(max_plot_depth)
    # 26C line
    if sensor == 'sci_water_temp' and config['gandalf']['plots']['use_26d']:
        logging.info('erddap_plot_sensor(): Using 26d line for %s' % vehicle)
        xvals = []
        yvals = []
        for index, row in data_frame.iterrows():
            if row['sci_water_temp'] < 26.05:
                if row['sci_water_temp'] > 25.95:
                    md = row['m_depth']
                    # Make it an epoch
                    epoch = mpd.datestr2num(row['m_present_time'])
                    xvals.append(epoch)
                    yvals.append(md)
        plt.plot(xvals, yvals,c='k')


    # SCATTER IT
    # check for alt_colormaps
    if alt_colormap:
        logging.debug('erddap_plot_sensor(): Using alt_colormap...')

    plt.scatter(mpd.datestr2num(data_frame['m_present_time']),
                data_frame['m_depth'], s=15, c=data_frame[sensor],
                lw=0, marker='8', cmap=cmap)
    plt.colorbar().set_label(config.get(
        sensor, record['unit_string']), fontsize=10)
    logging.debug("erddap_plot_sensor(): Setting CLIM to %0.2f, %0.2f" % (sensor_min, sensor_max))
    plt.clim(sensor_min, sensor_max)
    # no bottom for ERDDAP

    # add logo
    logo_file = config['gandalf']['plots']['logo_file']
    the_logo = plt.imread(logo_file)
    logo_loc = config['gandalf']['plots']['logo_loc']
    fig.figimage(the_logo, logo_loc[0], logo_loc[1], zorder=10)

    # save it
    logging.debug("erddap_plot_sensor(): %s is %s" % (vehicle, status))
    if status == 'deployed':
        plot_dir = config['gandalf']['plots']['deployed_plot_dir']
    else:
        plot_dir = config['gandalf']['plots']['postprocess_plot_dir']
    plot_file = "%s/%s.png" % (plot_dir, sensor)
    logging.info("erddap_plot_sensor(): Writing %s" % (plot_file))
    plt.savefig(plot_file, dpi=100)
    # close figure
    plt.close(fig)


def gandalf_gdac_plots(vehicle):
    """The boss."""
    register_cmocean()
    logging.info("make_erddap_plots(%s)" % vehicle)
    json_data = get_erddap_data(vehicle)
    if json_data:
        logging.info("make_erddap_plots(): get_data(%s) succeeded." % vehicle)
    else:
        logging.warn("make_erddap_plots(): get_data(%s) FAILED. " % vehicle)


    df = build_df(vehicle, json_data)
    config = get_vehicle_config(vehicle)
    plot_sensor_list = config['gandalf']['plots']['plot_sensor_list']
    for sensor in plot_sensor_list:
        plot_sensor(vehicle, sensor, df)


if __name__ == '__main__':
    vehicles = ['ru34']
    logging.basicConfig(level=logging.INFO)
    start_time = time.time()
    for vehicle in vehicles:
        gandalf_gdac_plots(vehicle)
    end_time = time.time()
    duration = end_time - start_time
    logging.info('Duration: %0.2f seconds' % duration)
