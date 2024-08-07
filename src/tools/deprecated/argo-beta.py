#!/usr/bin/env python3
"""3D viz of glider and ARGO data.

Author: robertdcurrier@gmail.com
Created: 2020-07-27
Modified: 2020-10-26
Notes: Moved to production. Getting feedback from users.
10-26: Migrated to logging and multiprocessing
"""
import json
import sys
import requests
import cmocean
import gsw
import gc
import logging
import time
import multiprocessing as mp
import numpy as np
import pandas as pd
import seawater as sw
import plotly.express as px
import matplotlib.pyplot as plt
from matplotlib import dates as mpd
from decimal import getcontext, Decimal
from calendar import timegm
from geojson import LineString, FeatureCollection, Feature, Point
from pandas.plotting import register_matplotlib_converters
from gandalf_utils import get_vehicle_config, get_sensor_config, flight_status


def register_cmocean():
    """Name: register_cmocean.

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
    """Convert cmocean color maps to Plotly colormaps.

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


def get_platform_profiles(platform_number):
    """get_platform_profiles.

    Created: 2020-06-05
    Modified: 2020-06-05
    Author: robertdcurrier@gmail.com
    Notes: Retrieves platform profiles via argovis API
    """
    # TO DO  config file for argovis url 2023-03-03 updated URL
    url = ('https://argovisbeta02.colorado.edu/catalog/platforms/{}'.
           format(platform_number))
    logging.debug('get_platform_profiles(%s)' % url)
    resp = requests.get(url)
    # Consider any status other than 2xx an error
    if not resp.status_code // 100 == 2:
        logging.debug('get_platform_profiles(): Unexpected response {}'.format(resp))
        return False
    platformProfiles = resp.json()
    return platformProfiles


def profiles_to_df(profiles):
    """Name: profiles_to_df.

    Created: 2020-06-04
    Modified: 2021-09-01
    Author: robertdcurrier@gmail.com
    Notes: Convert profiles in JSON to pandas df. Pretty much word for word
    from the Argovis API doco. Update: We added the return of profileDF
    so we have easy access to the last profile
    Added PI_NAME on 2021-09-01.
    """
    logging.info('profiles_to_df()...')
    pi_name = (profiles[0]['PI_NAME'])
    keys = profiles[0]['measurements'][0].keys()
    data_frame = pd.DataFrame(columns=keys)
    for profile in profiles:
        profileDf = pd.DataFrame(profile['measurements'])
        profileDf['pi'] = pi_name
        profileDf['cycle_number'] = profile['cycle_number']
        profileDf['profile_id'] = profile['_id']
        profileDf['lat'] = profile['lat']
        profileDf['lon'] = profile['lon']
        profileDf['date'] = profile['date']
        data_frame = pd.concat([data_frame, profileDf], sort=False)
    most_recent_date = data_frame.iloc[0]['date']
    oldest_date = data_frame.iloc[-1]['date']
    logging.debug("profiles_to_df(): Before sorting newest date: %s oldest date: %s" %
          (most_recent_date, oldest_date))
    logging.debug('profiles_to_df(): data_frame has %d rows' % len(data_frame))
    logging.debug('profiles_to_df(): Sorting data_frame by date DESC... just to be sure')
    data_frame = data_frame.sort_values(by=['date'], ascending=False)
    most_recent_date = data_frame.iloc[0]['date']
    oldest_date = data_frame.iloc[-1]['date']
    logging.debug("profiles_to_df(): After sorting newest date: %s oldest date: %s" %
          (most_recent_date, oldest_date))
    return data_frame


def dinkum_convert(dinkum_num):
    """Name:       dinkum_convert.

    Author:     bob.currier@gcoos.org
    Created:    2015-07-22
    Modified:   2015-07-22
    Inputs:     lon, lat in dddd.mm
    Outputs:    lon, lat in dd.ddd
    """
    logging.debug('dinkum_convert(%0.4f)' % dinkum_num)
    getcontext().prec = 6
    dinkum_num = Decimal(dinkum_num)
    dinkum_int = int((dinkum_num / Decimal(100.0)))
    dddd = Decimal((dinkum_int + (dinkum_num - (dinkum_int * 100)) /
                    Decimal(60.0)))
    return float(dddd)


def set_color_lims(vehicle, sensor, df):
    """Configure colorbar min/max.

    Author: robertdcurrier@gmail.com
    Created: 2020-07-29
    Modified: 2020-07-29
    Notes: Gets sensor config settings and drops rows < min and > max
    """
    logging.info('set_color_lims(%s, %s)' % (vehicle, sensor))
    sensor_config = (get_sensor_config(vehicle))
    for config in sensor_config:
        if (config['sensor'] == sensor):
            break
    logging.debug('set_color_lims(): Got config for %s' % sensor)
    sensor_min = config['sensor_plot_min']
    sensor_max = config['sensor_plot_max']
    logging.debug("set_color_lims(): Limits for %s are %0.4f min %0.4f max" %
          (sensor, sensor_min, sensor_max))
    logging.debug("set_color_lims(): %s before adjustment has %0.4f min %0.4f max" %
          (sensor, df[sensor].min(), df[sensor].max()))
    logging.debug("set_color_lims(): Adjusting df to min/max +/- 1")
    df = df[df[sensor] < sensor_max + 1]
    df = df[df[sensor] > sensor_min - 1]
    logging.debug("set_color_lims(): %s after adjustment has %0.4f min %0.4f max" %
          (sensor, df[sensor].min(), df[sensor].max()))
    return df


def get_cmocean_name(sensor):
    """get_cmocean_name.

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


def make_argo_fig(platform, sensor, sensor_df):
    """Fig for ARGO floats.

    Author:     bob.currier@gcoos.org
    Created:    2020-07-30
    Modified:   2020-08-26
    Notes: Working on migrating settings into config file
    """
    logging.debug("make_argo_fig(%s)" % platform)
    sdf_len = len(sensor_df)
    logging.debug("make_argo_fig(%s): sensor_df has %d rows" % (platform, sdf_len))
    if sensor == 'temp':
        logging.debug('make_argo_fig(): Using thermal for color map')
        cmap = 'thermal'
    if sensor == 'psal':
        logging.debug('make_argo_fig(): Using haline for color map')
        cmap = 'haline'
    colors = sensor_df[sensor]
    fig = px.scatter_3d(sensor_df, y='date', x='date',
                        z='z', color=colors, labels={
                            "z": "Depth(m)",
                            "date" : "",
                            }, height=900, color_continuous_scale=cmap)
    return fig


def plotly_argo_scatter(platform, sensor, sensor_df):
    """Use Plotly to make our live ARGO float scatter.

    Author:     bob.currier@gcoos.org
    Created:    2020-08-24
    Modified:   2020-08-24
    Notes: Working on migrating settings into config file
    """
    logging.info('plotly_argo_scatter(%s, %s)' % (platform, sensor))
    # Public names for sensors
    if sensor == 'temp':
        public_name = 'Water Temperature'
    if sensor == 'psal':
        public_name = 'Salinity'
    min_date = sensor_df['date'].min().split('T')[0]
    max_date = sensor_df['date'].max().split('T')[0]
    logging.debug("plotly_argo_scatter_sensor(): plotting %s" % sensor)
    logging.debug("plotly_argo_scatter(): start_date %s" % min_date)
    logging.debug("plotly_argo_scatter(): end_date %s" % max_date)

    logging.debug("plotly_ARGO_scatter(): df has initial length of %d" % len(sensor_df))
    # Need to figure out how to get line break in title or use subtitle
    subtitle1 = "<b>%s</b>" % (public_name)
    subtitle2 = "<i>%s to %s</i>" % (min_date, max_date)
    plot_title = "ARGO Float %s<br>%s<br>%s" % (platform, subtitle1, subtitle2)
    fig = make_argo_fig(platform, sensor, sensor_df)
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
    root_dir = '/data/gandalf/argo/plots'
    plot_file = "%s/%s_%s3D.html" % (root_dir, platform, sensor)
    logging.debug('plotly_ARGO_scatter(): Saving %s' % plot_file)
    fig.write_html(plot_file)
    logging.debug("-------------------------------------------------------------")


def add_z(data_frame):
    """Name: add_z.

    Created: 2020-06-04
    Modified: 2020-06-04
    Author: robertdcurrier@gmail.com
    Notes: Adds column 'Z' to data_frame and calculates using gsw function
    gsw.z_from_p
    """
    logging.debug('add_z(): Calculating z from p...')
    data_frame['z'] = 0
    for _ in data_frame:
        data_frame['z'] = gsw.z_from_p(data_frame['pres'],
                                       data_frame['lat'])
    return data_frame


def get_last_profile(platform_profiles):
    """Name: get_last_profile.

    Created: 2020-0703
    Modified: 2020-0703
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
    logging.warning('get_last_profile(): Last Date is %s' % platform_profiles[0]['date'])
    return last_profile


def config_date_axis():
    """Name: config_date_axis.

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


def argo_plot_sensor(platform, data_frame, sensor):
    """Get jiggy wit it."""
    # TO DO: config file for plot_dir
    logging.info('argo_plot_sensor(%s, %s)' % (platform, sensor))
    plot_dir = '/data/gandalf/argo/plots'
    fig = config_date_axis()
    df_len = (len(data_frame))
    if df_len == 0:
        logging.debug('argo_plot_sensor(): Empty Data Frame')
        return
    data_frame['date'] = (pd.to_datetime(data_frame['date']).dt.strftime
                          ('%Y-%m-%d'))
    min_date = data_frame['date'].min()
    max_date = data_frame['date'].max()
    logging.debug("argo_plot_sensor(): plotting %s" % sensor)
    logging.debug("argo_plot_sensor(): start_date %s" % min_date)
    logging.debug("argo_plot_sensor(): end_date %s" % max_date)

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
    title_string = "ARGO float %s\n%s" % (platform, subtitle_string)
    plt.title(title_string, fontsize=12, horizontalalignment='center')

    logging.debug('argo_plot_sensor(): Using colormap %s' % cmap)
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


def argo_plot_last_profile(platform, last_profile, sensor):
    """Name: argo_plot_last_profile.

    Created: 2020-06-09
    Modified: 2020-06-09
    Author: robertdcurrier@gmail.com
    Notes: Uses COASTAL code to generate standard CTD profile plots for most
    recent profile in slim_df
    TO DO: add config file
    """
    chart_name = "/data/gandalf/argo/plots/%s_%s_last.png" % (platform, sensor)
    logging.info('argo_plot_last_profile(): Plotting last profile for %s' % platform)
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
    plt.plot(last_profile[sensor], last_profile['z'], line_color)

    logging.debug("argo_plot_last_profile(): Saving %s" % chart_name)
    plt.savefig(chart_name)
    plt.close(fig)


def argo_surface_marker(platform, slim_df):
    """Name: argo_surface_marker.

    Created: 2020-06-05
    Modified: 2020-06-08
    Author: robertdcurrier@gmail.com
    Notes: Uses last date/time reported position to generate geoJSON
    feature. Feature is returned and added to features[]. When complete,
    features[] is made into a feature collection.
    TO DO: create argo.cfg and use instead of hardwiring...
    """
    logging.info('argo_surface_marker(%s): creating surface marker' % platform)
    coords = []
    features = []
    for index, row in slim_df.iterrows():
        point = Point([row['lon'], row['lat']])
        coords.append(point)

    most_recent = slim_df.iloc[0]
    date = most_recent['date']

    lat = most_recent['lat']
    lon = most_recent['lon']
    pi = most_recent['pi']
    point = Point([lon, lat])
    logging.debug("argo_surface_marker(): Generating track")
    track = LineString(coords)
    track = Feature(geometry=track, id='track')
    # features.append(track) <--- turned off until we can toggle uniques
    surf_marker = Feature(geometry=point, id='surf_marker')
    # plot names
    t_plot = '/data/gandalf/argo/plots/%s_temp.png' % platform
    s_plot = '/data/gandalf/argo/plots/%s_psal.png' % platform
    t_plot3D = '/data/gandalf/argo/plots/%s_temp3D.html' % platform
    s_plot3D = '/data/gandalf/argo/plots/%s_psal3D.html' % platform
    temp3d_icon = '/static/images/temp3d_icon.png'
    psal3d_icon = '/static/images/psal3d_icon.png'
    t_last = '/data/gandalf/argo/plots/%s_temp_last.png' % platform
    s_last = '/data/gandalf/argo/plots/%s_psal_last.png' % platform

    surf_marker.properties['platform'] = platform
    surf_marker.properties['html'] = """
        <h5><center><span class='infoBoxHeading'>ARGO Float Status</span></center></h5>
        <table class='infoBoxTable'>
            <tr><td class='td_infoBoxSensor'>Platform:</td><td>%s</td></tr>
            <tr><td class='td_infoBoxSensor'>PI:</td><td>%s</td></tr>
            <tr><td class='td_infoBoxSensor'>Date/Time:</td><td>%s</td></tr>
            <tr><td class='td_infoBoxSensor'>Position:</td><td>%0.4fW/%0.4fN</td></tr>
        </table>
        <div class = 'infoBoxBreakBar'>Most Recent Cycle</div>
        <div class = 'infoBoxLastPlotDiv'>
            <a href='%s' target="_blank">
                <img class = 'infoBoxLastPlotImage' src = '%s'></img>
            </a>
            <a href='%s' target="_blank">
                <img class = 'infoBoxLastPlotImage' src = '%s'></img>
            </a>
        </div>
        <div class = 'infoBoxBreakBar'>2D Time Series Plots</div>
        <div class = 'infoBoxPlotDiv'>
            <a href='%s' target="_blank">
                <img class = 'infoBoxPlotImage' src = '%s'></img>
            </a>
            <a href='%s' target="_blank">
                <img class = 'infoBoxPlotImage' src = '%s'></img>
            </a>
        </div>
        """ % (platform, pi, most_recent['date'], lon, lat, t_last, t_last,
               s_last, s_last, t_plot, t_plot, s_plot, s_plot)
    features.append(surf_marker)
    return features


def write_geojson_file(data):
    """Name: write_geojson.

    Created: 2020-06-05
    Modified: 2020-10-26
    Author: robertdcurrier@gmail.com
    Notes: writes out feature collection
    """
    fname = ("/data/gandalf/deployments/geojson/argo.json")
    logging.info("write_geojson(): Writing %s" % fname)
    outf = open(fname,'w')
    outf.write(str(data))
    outf.close()


def build_argo_plots(platform):
    """DOCSTRING."""
    argo_sensors = ['temp', 'psal']
    logging.info('build_argo_plots(): Processing platform %d' % platform)
    platform_profiles = get_platform_profiles(platform)
    # Only do this if we get good data...
    if platform_profiles:
        last_profile = get_last_profile(platform_profiles)
        add_z(last_profile)
        slim_df = profiles_to_df(platform_profiles)
        logging.debug('Dropping NaNs...')
        slim_df = slim_df.dropna()
        logging.debug("slim_df now has %d rows" % len(slim_df))
        add_z(slim_df)
        logging.debug("build_argo_plots(): Max PSAL is %0.4f" % max(slim_df['psal']))
        logging.debug("build_argo_plots(): Min PSAL is %0.4f" % min(slim_df['psal']))
        for sensor in argo_sensors:
            argo_plot_sensor(platform, slim_df, sensor)
            argo_plot_last_profile(platform, last_profile, sensor)
            logging.debug('Generating 3D plot for %s %s' % (platform, sensor))
            plotly_argo_scatter(platform, sensor, slim_df)
        surface_marker = argo_surface_marker(platform, slim_df)
        return(FeatureCollection(surface_marker))


def argo_process():
    """Name: init_app.

    Created: 2020-08-25
    Modified: 2020-08-25
    Author: robertdcurrier@gmail.com
    Notes: Main entry point. We now plot both 2D and 3D ARGO data
    """
    platform_list = [4902345, 4902467, 4903240, 4903232, 4903356,
            4903249, 4902350, 4902354, 4903255, 4903277,
            4903353, 4903333, 4901719, 4902912, 4903233, 4903252,
            4903248, 4903354, 4901716, 4903622, 4903624]
    argo_features = []
    #platform_list = [4903622, 4903624]  # <-- For speedy testing
    # register helpers
    register_matplotlib_converters()
    register_cmocean()

    for platform in platform_list:
        argo_features.append(build_argo_plots(platform))
    write_geojson_file(argo_features)


if __name__ == '__main__':
    # Need to add argparse so we can do singles without editing...
    logging.basicConfig(level=logging.INFO)
    start_time = time.time()
    argo_process()
    end_time = time.time()
    minutes = ((end_time - start_time) / 60)
    logging.warning('Duration: %0.2f minutes' % minutes)
