#!/usr/bin/env python3
"""
Author:     robertdcurrier@gmail.com
Created:    2024-01-24
Modified:   2024-01-26
Notes:      Gets CSV file from WHOI. Creates df from csv. Inserts
            into MongoDB rejecting dupes. Creates track and last_pos
            for UGOS floats.
            TO DO: get unique platform IDs from DF. Do a
            for platform in platforms:  loop to build final json
"""
import json
import random
import sys
import os
import requests
import cmocean
import gsw
import gc
import logging
import time
import wget
import glob
import multiprocessing as mp
import numpy as np
import pandas as pd
import seawater as sw
import plotly.express as px
import matplotlib.pyplot as plt
import datetime
from datetime import date
from datetime import timedelta
from matplotlib import dates as mpd
from decimal import getcontext, Decimal
from calendar import timegm
from geojson import LineString, FeatureCollection, Feature, Point
from pandas.plotting import register_matplotlib_converters
from pymongo import MongoClient
from pymongo import errors

# THESE SETTINGS NEED TO COME FROM CONFIG FILE EVENTUALLY
ROOT_DIR = ''
using_multiprocess = True
dataDays = 30
numProcesses = 8
date_cutoff = 21
# END GLOBALS


def connect_mongo():
    """
    DOCSTRING
    """
    client = MongoClient('mongo:27017')
    return client


def register_cmocean():
    """
    Created: 2020-06-04
    Modified: 2020-06-04
    Author: robertdcurrier@gmail.com
    Notes: Registers Kristin's oceanographic color map
    """
    logging.debug('register_cmocean(): Installing cmocean color maps')
    plt.register_cmap(name='thermal', cmap=cmocean.cm.thermal)
    plt.register_cmap(name='haline', cmap=cmocean.cm.haline)
    plt.register_cmap(name='algae', cmap=cmocean.cm.algae)
    plt.register_cmap(name='matter', cmap=cmocean.cm.matter)
    plt.register_cmap(name='dense', cmap=cmocean.cm.dense)
    plt.register_cmap(name='oxy', cmap=cmocean.cm.oxy)
    plt.register_cmap(name='speed', cmap=cmocean.cm.speed)


def cmocean_to_plotly(cmap, pl_entries):
    """
    Author: robertdcurrier@gmail.com (via Plotly Docs)
    Created: 2020-08-18
    Modified: 2020-08-18
    Notes: Had to add list() as the docs were written for Python2
    """
    h = 1.0/(pl_entries-1)
    pl_colorscale = []

    for k in range(pl_entries):
        C = list(map(np.uint8, np.array(cmap(k*h)[:3])*255))
        pl_colorscale.append([k*h, 'rgb'+str((C[-1], C[1], C[2]))])
    logging.debug('cmocean_to_plotly(): Generated %d mappings' % len(pl_colorscale))
    return pl_colorscale


def combine_dfs(dfs):
    """
    Created: 2024-01-23
    Modified: 2024-01-23
    Author: robertdcurrier@gmail.com
    Notes: Combines all dfs into single df and
    returns a merged dataframe
    """
    logging.info(f'combine_dfs()')
    combined_df = pd.concat(dfs, axis=1)
    combined_df = combined_df.loc[:,~combined_df.columns.duplicated()]

    return combined_df


def get_platform_profiles(platform):
    """
    Created: 2024-01-23
    Modified: 2024-02-03
    Author: robertdcurrier@gmail.com
    Notes: Retrieves platform profiles via ugos API
    Returns a merged dataframe
    """
    ugos_dfs = []
    # TO DO  config file file names and other parameters
    ugos_file = 'last72h.fhd.csv'
    output_dir = '/data/gandalf/ugos/csv'
    # empty dir as wget in Python doesn't have an -O option
    files = glob.glob(f'{output_dir}/*.csv')

    #For testing we skip this so we don't keep hammering the WHOI server
    for f in files:
        logging.info(f'get_platform_profiles(): Removing {f}')
        os.remove(f)

    logging.info(f'get_platform_profiles({ugos_file})')
    url = (f'https://map2.woodsholegroup.com/ugos/in_situ/{ugos_file}')
    wget.download(url, out=output_dir)
    csv_file = f'{output_dir}/{ugos_file}'
    df = pd.read_csv(csv_file)
    # drop all other platform than the current one
    df = df.loc[df['id'] == platform]

    if df.empty:
        logging.warning('get_platform_profiles(): Unexpected Empty Dataframe')
        sys.exit()
    return df


def get_cmocean_name(sensor):
    """
    Author: robertdcurrier@gmail.com
    Created: 2020-08-18
    Modified: 2020-08-18
    Notes: Crude mapping of cmocean names so we can use sensor.json string
    Need to make this a lookup table..although this does work...
    """
    if sensor == 'temp':
        cmap = cmocean.cm.thermal
    if sensor == 'psal':
        cmap = cmocean.cm.haline
    return cmap


def make_ugos_fig(platform, sensor, sensor_df):
    """
    Author:     bob.currier@gcoos.org
    Created:    2020-07-30
    Modified:   2020-08-26
    Notes: Working on migrating settings into config file
    """
    logging.debug("make_ugos_fig(%s)" % platform)
    sdf_len = len(sensor_df)
    logging.debug("make_ugos_fig(%s): sensor_df has %d rows" % (platform, sdf_len))
    if sensor == 'temp':
        logging.debug('make_ugos_fig(): Using thermal for color map')
        cmap = 'thermal'
    if sensor == 'psal':
        logging.debug('make_ugos_fig(): Using haline for color map')
        cmap = 'haline'
    colors = sensor_df[sensor]
    fig = px.scatter_3d(sensor_df, y='date', x='date',
                        z='z', color=colors, labels={
                            "z": "Depth(m)",
                            "date" : "",
                            }, height=900, color_continuous_scale=cmap)
    return fig


def plotly_ugos_scatter(platform, sensor, sensor_df):
    """
    Author:     bob.currier@gcoos.org
    Created:    2020-08-24
    Modified:   2020-08-24
    Notes: Working on migrating settings into config file
    """
    logging.info('plotly_ugos_scatter(%s, %s)' % (platform, sensor))
    # Public names for sensors
    if sensor == 'temp':
        public_name = 'Water Temperature'
    if sensor == 'psal':
        public_name = 'Salinity'
    min_date = sensor_df['date'].min().split('T')[0]
    max_date = sensor_df['date'].max().split('T')[0]
    logging.debug("plotly_ugos_scatter_sensor(): plotting %s" % sensor)
    logging.debug("plotly_ugos_scatter(): start_date %s" % min_date)
    logging.debug("plotly_ugos_scatter(): end_date %s" % max_date)

    logging.debug("plotly_ugos_scatter(): df has initial length of %d" % len(sensor_df))
    # Need to figure out how to get line break in title or use subtitle
    subtitle1 = "<b>%s</b>" % (public_name)
    subtitle2 = "<i>%s to %s</i>" % (min_date, max_date)
    plot_title = "ugos Float %s<br>%s<br>%s" % (platform, subtitle1, subtitle2)
    fig = make_ugos_fig(platform, sensor, sensor_df)
    # marker_line_width and marker_size should be in config file
    fig.update_traces(mode='markers', marker_line_width=0, marker_size=4)
    # Tweak title font and size
    fig.update_layout(
                      title={'text': plot_title, 'y': 0.9, 'x': 0.5,
                             'xanchor': 'center',
                             'yanchor': 'top',
                             'font_family': 'Times New Roman',
                             'font_size': 12})
    # save it
    root_dir = ROOT_DIR + '/data/gandalf/ugos/plots'
    plot_file = "%s/%s_%s3D.html" % (root_dir, platform, sensor)
    logging.debug('plotly_ugos_scatter(): Saving %s' % plot_file)
    fig.write_html(plot_file)
    logging.debug("-------------------------------------------------------------")


def get_last_profile(platform, platform_profiles):
    """
    Created: 2020-07-03
    Modified: 2020-07-03
    Author: robertdcurrier@gmail.com
    Notes: Extracts last profile from all profiles for plotting
    """
    logging.debug("get_last_profile()...")
    last_profile = pd.DataFrame(platform_profiles[0]['measurements'])
    last_profile['cycle_number'] = platform_profiles[0]['cycle_number']
    last_profile['profile_id'] = platform_profiles[0]['_id']
    last_profile['lat'] = platform_profiles[0]['lat']
    last_profile['lon'] = platform_profiles[0]['lon']
    last_profile['date'] = platform_profiles[0]['date']
    logging.info('get_last_profile(%s): Last Date is %s',
                    platform, platform_profiles[0]['date'])
    return last_profile


def config_date_axis():
    """
    Created: 2020-06-04
    Modified: 2020-06-04
    Author: robertdcurrier@gmail.com
    Notes: Sets up date/time x axis
    """
    # instantiate the plot
    fig = plt.figure(figsize=(14, 6))
    gca = plt.gca()
    # make room for xlabel
    plt.subplots_adjust(bottom=0.15)
    # labels
    plt.ylabel('Depth (m)')
    # ticks
    # hours = mpd.HourLocator(interval = 6)
    logging.debug("config_date_axis(): Setting x axis for date/time display")
    gca.xaxis.set_tick_params(which='major')
    plt.setp(gca.xaxis.get_majorticklabels(), rotation=45, fontsize=6)
    major_formatter = mpd.DateFormatter('%Y/%m/%d')
    # gca.xaxis.set_major_locator(hours)
    gca.xaxis.set_major_formatter(major_formatter)
    gca.set_xlabel('Date', fontsize=12)

    return fig


def ugos_plot_sensor(platform, data_frame, sensor):
    """
    Created:  2020-06-04
    Modified: 2020-06-04
    Author:   robertdcurrier@gmail.com
    Notes:    plots sensor data, d'oh
    """
    # TO DO: config file for plot_dir
    logging.info('ugos_plot_sensor(%s, %s)' % (platform, sensor))
    plot_dir = ROOT_DIR + '/data/gandalf/ugos/plots'
    fig = config_date_axis()
    df_len = (len(data_frame))
    if df_len == 0:
        logging.debug('ugos_plot_sensor(): Empty Data Frame')
        return
    data_frame['date'] = (pd.to_datetime(data_frame['date']).dt.strftime
                          ('%Y-%m-%d'))
    min_date = data_frame['date'].min()
    max_date = data_frame['date'].max()
    logging.debug("ugos_plot_sensor(): plotting %s" % sensor)
    logging.debug("ugos_plot_sensor(): start_date %s" % min_date)
    logging.debug("ugos_plot_sensor(): end_date %s" % max_date)

    # SCATTER IT
    dates = [pd.to_datetime(d) for d in data_frame['date']]
    # We COULD add these to config file but since we'll only ever plot T & S...
    if sensor == 'temp':
        cmap = 'thermal'
        unit_string = "($^oC$)"
        sensor_name = 'Water Temperature'
    if sensor == 'psal':
        cmap = 'haline'
        unit_string = "PPT (10$^{-3}$)"
        sensor_name = "Salinity"

    subtitle_string = "%s %s" % (sensor_name, unit_string)
    title_string = "ugos float %s\n%s" % (platform, subtitle_string)
    plt.title(title_string, fontsize=12, horizontalalignment='center')

    logging.debug('ugos_plot_sensor(): Using colormap %s' % cmap)
    plt.scatter(dates, data_frame['z'], s=15, c=data_frame[sensor],
                lw=0, marker='8', cmap=cmap)
    plt.colorbar().set_label(unit_string, fontsize=10)
    plot_file = '%s/%s_%s.png' % (plot_dir, platform, sensor)
    logging.debug("plot_sensor(): Saving %s" % plot_file)
    plt.savefig(plot_file, dpi=100)
    # close figure
    plt.close(fig)
    logging.debug("plot_sensor(): Collecting garbage...")
    gc.collect()


def ugos_plot_last_profile(platform, last_profile, sensor):
    """
    Created: 2020-06-09
    Modified: 2020-06-09
    Author: robertdcurrier@gmail.com
    Notes: Uses COASTAL code to generate standard CTD profile plots for most
    recent profile in slim_df
    TO DO: add config file
    """
    chart_name = ROOT_DIR + "/data/gandalf/ugos/plots/%s_%s_last.png" % (platform, sensor)
    logging.info('ugos_plot_last_profile(): Plotting last profile for %s' % platform)
    # Begin plot config
    title_fs = 10
    suptitle_fs = 12
    title_style = 'italic'
    xlabel_fs = 12
    ylabel_fs = 10
    fs = (5, 8)
    # We COULD add these to config file but since we'll only ever plot T & S...
    if sensor == 'temp':
        unit_string = "($^oC$)"
        sensor_name = 'Water Temperature'
        line_color = 'blue'
    if sensor == 'psal':
        unit_string = "PPT (10$^{-3}$)"
        sensor_name = "Salinity"
        line_color = 'red'
    # End plot config

    fig = plt.figure(figsize=(fs))
    gca = plt.gca()
    gca.set_ylabel('depth (m)', fontsize=ylabel_fs, labelpad=-5)
    gca.set_xlabel(unit_string, fontsize=xlabel_fs)
    plt.suptitle(sensor_name, fontsize=suptitle_fs,
                 horizontalalignment='center')
    title_string = 'Platform %s at %s' % (platform, last_profile.iloc[0]
                                          ['date'])
    plt.title(title_string, fontsize=title_fs, style=title_style,
              horizontalalignment='center')
    logging.info("""plot_last_sensor(): last_profile[sensor].isna().any():
                 {}, sensor: {}, platform: {}""".format(last_profile[sensor].
                 isna().any(), sensor, platform))

    plt.plot(last_profile[sensor].fillna(0), last_profile['z'], line_color)

    logging.debug("ugos_plot_last_profile(): Saving %s" % chart_name)
    plt.savefig(chart_name)
    plt.close(fig)


def ugos_surface_marker(platform):
    """
    Created: 2020-06-05
    Modified: 2024-01-25
    Author: robertdcurrier@gmail.com
    Notes: Uses last date/time reported position to generate geoJSON
    feature. Feature is returned and added to features[]. When complete,
    features[] is made into a feature collection.
    TO DO: create ugos.cfg and use instead of hardwiring...
    """
    client = connect_mongo()
    db = client.gandalf
    collection = f'ugos_{platform}'

    list_cursor =  list(db[collection].find())
    df = pd.DataFrame(list_cursor).drop(columns=['_id'])
    df = df.sort_values(by=['t_utc'], ascending=True)
    logging.info(f'ugos_surface_marker({platform}): {len(df)} records')

    logging.info('ugos_surface_marker(%s): creating surface marker' % platform)
    coords = []
    features = []
    today = datetime.datetime.today()
    for index, row in df.iterrows():
        point = Point([row['lon_dd'], row['lat_dd']])
        coords.append(point)
    df = df.sort_values(by=['t_utc'], ascending=False)

    most_recent = df.iloc[0]
    last_date = datetime.datetime.strptime(most_recent['t_utc'],"%Y-%m-%d %H:%M:%S")
    delta = (today - last_date)
    delta_days = delta.days
    if delta_days > date_cutoff:
        logging.warning('ugos_surface_marker(%s): Stale data. Not appending.',
                        platform)

    lat = most_recent['lat_dd']
    lon = most_recent['lon_dd']
    pi = "UGOS"
    point = Point([lon, lat])
    logging.debug("ugos_surface_marker(): Generating track")
    track = LineString(coords)
    track = Feature(geometry=track, id='track')
    features.append(track)
    surf_marker = Feature(geometry=point, id='surf_marker')
    # plot names
    t_plot = ROOT_DIR + '/data/gandalf/ugos/plots/%s_temp.png' % platform
    s_plot = ROOT_DIR + '/data/gandalf/ugos/plots/%s_psal.png' % platform
    t_plot3D = ROOT_DIR + '/data/gandalf/ugos/plots/%s_temp3D.html' % platform
    s_plot3D = ROOT_DIR + '/data/gandalf/ugos/plots/%s_psal3D.html' % platform
    temp3d_icon = ROOT_DIR + '/static/images/temp3d_icon.png'
    psal3d_icon = ROOT_DIR + '/static/images/psal3d_icon.png'
    t_last = ROOT_DIR + '/data/gandalf/ugos/plots/%s_temp_last.png' % platform
    s_last = ROOT_DIR + '/data/gandalf/ugos/plots/%s_psal_last.png' % platform

    surf_marker.properties['platform'] = platform
    surf_marker.properties['html'] = """
        <h5><center><span class='infoBoxHeading'>UGOS Float Status</span></center></h5>
        <table class='infoBoxTable'>
            <tr><td class='td_infoBoxSensor'>Platform:</td><td>%s</td></tr>
            <tr><td class='td_infoBoxSensor'>PI:</td><td>%s</td></tr>
            <tr><td class='td_infoBoxSensor'>Date/Time:</td><td>%s</td></tr>
            <tr><td class='td_infoBoxSensor'>Position:</td><td>%0.4fW/%0.4fN</td></tr>
        </table>
        """ % (platform, pi, last_date, lon, lat)
    features.append(surf_marker)
    logging.info('ugos_surface_marker(%s): Most Recent Date is %s',
                    platform, last_date)
    return FeatureCollection(features)


def write_geojson_file(data):
    """
    Created: 2020-06-05
    Modified: 2020-10-26
    Author: robertdcurrier@gmail.com
    Notes: writes out feature collection
    """
    fname = (ROOT_DIR + "/data/gandalf/deployments/geojson/ugos.json")
    logging.warning("write_geojson(): Writing %s" % fname)
    outf = open(fname,'w')
    outf.write(str(data))
    outf.close()


def build_ugos_plots(platform):
    """
    Created:  2020-06-05
    Modified: 2022-09-08
    Author:   robertdcurrier@gmail.com
    Notes:    writes out feature collection
    """
    # because of multiprocessing, check if the value has been registered
    if 'thermal' not in plt.colormaps():
        register_cmocean()

    ugos_sensors = ['temp', 'psal']
    logging.warning('build_ugos_plots(): Processing platform %d' % platform)
    platform_profiles = get_platform_profiles(platform)
    # Only do this if we get good data...
    if platform_profiles:
        last_profile = get_last_profile(platform, platform_profiles)
        add_z(last_profile)
        slim_df = profiles_to_df(platform_profiles)

        for sensor in ugos_sensors:
            # if any column is none, drop the float and continue
            if sensor in slim_df.columns and slim_df[sensor].isna().all():
                logging.warning('build_ugos_plots(): Empty %s for %d',
                                sensor, platform)
                return False

        logging.debug('Dropping NaNs...')
        slim_df = slim_df.dropna()
        logging.info("build_ugos_plots(): slim_df now has %d rows" % len(slim_df))
        add_z(slim_df)

        if 'psal' in slim_df.columns:
            logging.debug("build_ugos_plots(): Max PSAL is %0.4f" % max(slim_df['psal']))
            logging.debug("build_ugos_plots(): Min PSAL is %0.4f" % min(slim_df['psal']))

        for sensor in ugos_sensors:
            ugos_plot_sensor(platform, slim_df, sensor)
            ugos_plot_last_profile(platform, last_profile, sensor)
            #logging.info('Generating 3D plot for %s %s' % (platform, sensor))
            # 2023-09-06 disabled temporarily by rdc
            #plotly_ugos_scatter(platform, sensor, slim_df)
        surface_marker = ugos_surface_marker(platform, slim_df)
        return(FeatureCollection(surface_marker))


def df_to_mongo(float, df):
    """
    Created:    2024-01-26
    Modified:   2024-01-26
    Author:     robertdcurrier@gmail.com
    Notes:      We first query the existing data and convert
                to a dataframe. We drop duplicates between df and
                existing df before performing insert_many. This
                seems inelegant but is better than dealing with
                index errors on insert being thrown by pymongo.
    """
    df = df.sort_values(by=['t_utc'], ascending=True)

    # Mongo connectivity
    client = connect_mongo()
    db = client.gandalf
    collection = f'ugos_{float}'
    db[collection].create_index('t_utc', unique = True) # skip if exists

    list_cursor =  list(db[collection].find())
    ugos_json = json.loads(df.to_json(orient='records'))


    # 2023-02-17: Now using collection per float
    logging.info(f'gandalf_ugos_floats(): Inserting into {collection}')
    try:
        db[collection].insert_many(ugos_json,ordered=False)
    except errors.BulkWriteError as e:
        logging.debug(f'{e.details}')


def ugos_process():
    """
    Created: 2024-01-23
    Modified: 2024-01-23
    Author: robertdcurrier@gmail.com
    Notes: Main entry point. We now plot both 2D and 3D ugos data
    """
    platform = 8955
    logging.info('ugos_process(): Registering helpers')
    # register helpers
    register_matplotlib_converters()

    df = get_platform_profiles(platform)
    df_to_mongo(platform, df)

    ugos_features = ugos_surface_marker(platform)

    write_geojson_file(ugos_features)



if __name__ == '__main__':
    # Need to add argparse so we can do singles without editing...
    logging.basicConfig(level=logging.INFO)
    start_time = time.time()
    ugos_process()
    end_time = time.time()
    minutes = ((end_time - start_time) / 60)
    logging.warning('Duration: %0.2f minutes' % minutes)
