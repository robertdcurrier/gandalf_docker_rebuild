#!/usr/bin/env python3
"""3D viz of seatrec data.

Author:     robertdcurrier@gmail.com
Created:    2023-02-20
Modified:   2023-03-23
Notes:      Started work on generating upcasts and downcasts for eventual
            submission to NDBC/GTS
"""
import json
import sys
import requests
import cmocean
import gsw
import gc
import logging
import time
import csv
import multiprocessing as mp
import numpy as np
import pandas as pd
import seawater as sw
import plotly.express as px
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from urllib.request import urlopen
from matplotlib import dates as mpd
from datetime import datetime
from decimal import getcontext, Decimal
from calendar import timegm
from geojson import LineString, FeatureCollection, Feature, Point
from pandas.plotting import register_matplotlib_converters
from netCDF4 import Dataset, stringtochar
from gandalf_utils import get_vehicle_config, get_sensor_config, flight_status
#GLOBALS
seatrec_root_url = "http://35.247.25.81/SEATREC"


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


def get_platform_profiles(platform):
    """get_platform_profiles via CSV.

    Created: 2023-02-20
    Modified: 2023-02-20
    Author: robertdcurrier@gmail.com
    Notes: Retrieves platform profiles via seatrec API
    """
    # TO DO  config file for seatrecvis url
    url = ('http://35.247.25.81/SEATREC/%s_ts.txt') % platform
    logging.debug('get_platform_profiles(%s)' % url)
    try:
        resp = requests.get(url)
    except:
        logging.warning('get_platform_profiles(%s): Error fetching URL', platform)
    # Consider any status other than 2xx an error
    if not resp.status_code // 100 == 2:
        logging.warning('get_platform_profiles(): Unexpected response {}'.format(resp))
        return False
    decoded_content = resp.content.decode('utf-8')
    cr = csv.reader(decoded_content.splitlines(), delimiter=',')
    my_csv = list(cr)

    return my_csv


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


def make_seatrec_fig(platform, sensor, sensor_df):
    """Fig for seatrec floats.

    Author:     bob.currier@gcoos.org
    Created:    2020-07-30
    Modified:   2020-08-26
    Notes: Working on migrating settings into config file
    """
    logging.info("make_seatrec_fig(%s)" % platform)
    sdf_len = len(sensor_df)
    logging.debug("make_seatrec_fig(%s): sensor_df has %d rows" % (platform, sdf_len))
    if sensor == 'Temperature(C)':
        logging.debug('make_seatrec_fig(): Using thermal for color map')
        cmap = 'thermal'
    if sensor == 'salinity(PSU)':
        logging.debug('make_seatrec_fig(): Using haline for color map')
        cmap = 'haline'
    colors = sensor_df[sensor]

    fig = px.scatter_3d(sensor_df, y='date', x='date',
                        z=sensor_df['z'], color=colors, labels={
                            "z": "Depth(m)",
                            "date" : "",
                            }, height=900, color_continuous_scale=cmap)

    return fig


def plotly_seatrec_3D(platform, sensor, sensor_df):
    """Use Plotly to make our live seatrec float scatter.

    Author:     bob.currier@gcoos.org
    Created:    2020-08-24
    Modified:   2023-02-20
    Notes: Working on migrating settings into config file
    """
    logging.info('plotly_seatrec_3D(%s, %s)' % (platform, sensor))
    # Public names for sensors
    if sensor == 'Temperature(C)':
        public_name = 'Water Temperature'
    if sensor == 'salinity(PSU)':
        public_name = 'Salinity'
    min_date = sensor_df['date'].min().split('T')[0]
    max_date = sensor_df['date'].max().split('T')[0]
    logging.info("plotly_seatrec_3D(): plotting %s" % sensor)
    logging.info("plotly_seatrec_3D(): start_date %s" % min_date)
    logging.info("plotly_seatrec_3D(): end_date %s" % max_date)

    logging.debug("plotly_seatrec_scatter(): df has initial length of %d" % len(sensor_df))
    # Need to figure out how to get line break in title or use subtitle
    subtitle1 = "<b>%s</b>" % (public_name)
    subtitle2 = "<i>%s to %s</i>" % (min_date, max_date)
    plot_title = "Seatrec Float %s<br>%s<br>%s" % (platform, subtitle1, subtitle2)
    sensor_df['depth(m)'] = sensor_df['depth(m)']*-1
    fig = make_seatrec_fig(platform, sensor, sensor_df)

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
    root_dir = '/data/gandalf/seatrec/plots'
    plot_file = "%s/%s_%s3D.html" % (root_dir, platform, sensor)
    logging.debug('plotly_seatrec_scatter(): Saving %s' % plot_file)
    fig.write_html(plot_file)
    logging.debug("-------------------------------------------------------------")


def get_last_seatrec_profile(platform, platform_df):
    """Name: get_last_seatrec_profile.

    Created: 2023-02-21
    Modified: 2023-02-21
    Author: robertdcurrier@gmail.com
    Notes: Extracts last profile from all profiles for plotting
    """
    logging.info("get_last_seatrec_profile(%s)", platform)
    last_profile_n = platform_df['Profile Number'].max()
    logging.info("get_last_seatrec_profile(%s): Last Profile Number is %d",
                 platform, last_profile_n)
    last_profile = (platform_df.loc[platform_df['Profile Number'] ==
                    last_profile_n])
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


def seatrec_plot_sensor(platform, platform_df, sensor):
    """Get jiggy wit it."""
    # TO DO: config file for plot_dir
    logging.info('seatrec_plot_sensor(%s, %s)' % (platform, sensor))
    plot_dir = '/data/gandalf/seatrec/plots'
    fig = config_date_axis()
    df_len = (len(platform_df))
    if df_len == 0:
        logging.debug('seatrec_plot_sensor(): Empty Data Frame')
        return

    min_date = platform_df['date'].min()
    max_date = platform_df['date'].max()
    logging.info("seatrec_plot_sensor(%s): plotting %s", platform, sensor)
    logging.info("seatrec_plot_sensor(%s): start_date %s", platform, min_date,)
    logging.info("seatrec_plot_sensor(%s): end_date %s", platform, max_date)

    # SCATTER IT
    dates = [pd.to_datetime(d) for d in platform_df['date']]
    # We COULD add these to config file but since we'll only ever plot T & S...
    if sensor == 'Temperature(C)':
        cmap = 'thermal'
        unit_string = "($^oC$)"
        sensor_name = 'Water Temperature'
    if sensor == 'salinity(PSU)':
        cmap = 'haline'
        unit_string = "PPT (10$^{-3}$)"
        sensor_name = "Salinity"

    subtitle_string = "%s %s" % (sensor_name, unit_string)
    title_string = "seatrec float %s\n%s" % (platform, subtitle_string)
    plt.title(title_string, fontsize=12, horizontalalignment='center')

    logging.debug('seatrec_plot_sensor(): Using colormap %s' % cmap)
    plt.scatter(dates, platform_df['z'], s=15, c=platform_df[sensor],
                lw=0, marker='8', cmap=cmap)
    plt.colorbar().set_label(unit_string, fontsize=10)
    plot_file = '%s/%s_%s.png' % (plot_dir, platform, sensor)
    add_seatrec_logo(platform, fig)

    logging.debug("plot_sensor(): Saving %s" % plot_file)
    plt.savefig(plot_file, dpi=100)
    # close figure
    plt.close(fig)
    logging.debug("plot_sensor(): Collecting garbage...")
    gc.collect()


def add_seatrec_logo(vehicle,fig):
    """
    Cleaning up plot_sensor and refactoring. Herein lies the logo part
    """
    logging.info('add_logo(%s)' % vehicle)
    logo_file='/data/gandalf/static/images/logos/seatrec-logo.png'
    the_logo = plt.imread(logo_file)
    logo_loc = [175, 90]
    plt.figimage(the_logo, logo_loc[0], logo_loc[1], zorder=10)


def seatrec_plot_last_profile(platform, last_profile, sensor):
    """Name: seatrec_plot_last_profile.

    Created: 2020-06-09
    Modified: 2023-02-21
    Author: robertdcurrier@gmail.com
    Notes: Uses COASTAL code to generate standard CTD profile plots for most
    recent profile in slim_df
    TO DO: add config file
    """
    chart_name = "/data/gandalf/seatrec/plots/%s_%s_last.png" % (platform, sensor)
    logging.info('seatrec_plot_last_profile(%s): Plotting %s', platform, sensor)
    # Begin plot config
    title_fs = 10
    suptitle_fs = 12
    title_style = 'italic'
    xlabel_fs = 12
    ylabel_fs = 10
    fs = (5, 8)
    # We COULD add these to config file but since we'll only ever plot T & S...
    if sensor == 'Temperature(C)':
        unit_string = "($^oC$)"
        sensor_name = 'Water Temperature'
        line_color = 'blue'
    if sensor == 'salinity(PSU)':
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
    title_string = 'Platform %s at %s' % (platform, last_profile['date'].max())
    plt.title(title_string, fontsize=title_fs, style=title_style,
              horizontalalignment='center')
    plt.plot(last_profile[sensor], last_profile['z'], line_color)

    logging.debug("seatrec_plot_last_profile(): Saving %s" % chart_name)
    plt.savefig(chart_name)
    plt.close(fig)


def seatrec_surface_marker(platform, platform_df):
    """Name: seatrec_surface_marker.

    Created: 2020-06-05
    Modified: 2023-02-20
    Author: robertdcurrier@gmail.com
    Notes: Uses last date/time reported position to generate geoJSON
    feature. Feature is returned and added to features[]. When complete,
    features[] is made into a feature collection.
    TO DO: create seatrec.cfg and use instead of hardwiring...
    """
    logging.info('seatrec_surface_marker(%s): creating surface marker' % platform)
    coords = []

    for index, row in platform_df.iterrows():
        point = Point([row['lon'], row['lat']])
        coords.append(point)

    # Most recent profile
    max_date = platform_df.iloc[-1]['date']
    lat = platform_df.iloc[-1]['lat']
    lon = platform_df.iloc[-1]['lon']

    pi = 'Chao, Yi'
    point = Point([lon, lat])
    logging.debug("seatrec_surface_marker(): Generating track")
    track = LineString(coords)
    track = Feature(geometry=track, id='track')
    # features.append(track) <--- turned off until we can toggle uniques
    surf_marker = Feature(geometry=point, id='surf_marker')
    # plot names
    t_plot = '/data/gandalf/seatrec/plots/%s_Temperature(C).png' % platform
    s_plot = '/data/gandalf/seatrec/plots/%s_salinity(PSU).png' % platform
    t_plot3D = '/data/gandalf/seatrec/plots/%s_temp3D.html' % platform
    s_plot3D = '/data/gandalf/seatrec/plots/%s_psal3D.html' % platform
    temp3d_icon = '/static/images/temp3d_icon.png'
    psal3d_icon = '/static/images/psal3d_icon.png'
    t_last = '/data/gandalf/seatrec/plots/%s_Temperature(C)_last.png' % platform
    s_last = '/data/gandalf/seatrec/plots/%s_salinity(PSU)_last.png' % platform

    surf_marker.properties['platform'] = platform
    surf_marker.properties['html'] = """
        <h5><center><span class='infoBoxHeading'>Seatrec Float Status</span></center></h5>
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
        """ % (platform, pi, max_date, lon, lat, t_last, t_last,
               s_last, s_last, t_plot, t_plot, s_plot, s_plot)
    return surf_marker


def write_geojson_file(data):
    """Name: write_geojson.

    Created: 2020-06-05
    Modified: 2020-10-26
    Author: robertdcurrier@gmail.com
    Notes: writes out feature collection
    """
    fname = ("/data/gandalf/deployments/geojson/seatrec.json")
    logging.info("write_geojson(): Writing %s" % fname)
    outf = open(fname,'w')
    outf.write(str(data))
    outf.close()


def profiles_to_df(profiles):
    """
    Created: 2023-02-20
    Modified: 2023-02-20
    Author: robertdcurrier@gmail.com
    Notes: Convert profiles in CSV to pandas df.
    """
    logging.info('profiles_to_df()...')
    # Get column names
    headers = profiles[0]
    # Drop column names so we don't have dupes
    profiles = profiles[1:]
    data_frame = pd.DataFrame(profiles, columns=headers)
    # These need to go into config file eventually
    data_frame = data_frame.astype({'Temperature(C)':'float',
                                    'salinity(PSU)':'float',
                                    'lon':'float', 'lat':'float',
                                    'depth(m)':'float',
                                    'Profile Number':'float'})
    # Create a date column for us to use
    data_frame['date'] = (pd.to_datetime(data_frame['time(UTC)']).dt.strftime
                          ('%Y-%m-%d'))

    return data_frame


def gen_seatrec_profiles(platform, platform_df):
    """
    Created:    2023-03-23
    Modified:   2023-03-23
    Author:     robertdcurrier@gmail.com
    Notes:      Iterates over platform_df and seeks out all downcasts
    """
    logging.info('gen_seatrec_profiles(%s)', platform)
    maxp = int(platform_df['Profile Number'].max())
    logging.info('gen_seatrec_profiles(%s): %d profiles', platform, maxp)
    idx = 1
    while idx <= maxp:
        df = platform_df.loc[(platform_df['Profile Number'] == idx)]
        create_profile(platform, df.to_xarray(), idx)
        idx+=1


def create_profile(platform, seatrec_xr, profile):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-07-29
    Modified:   2023-03-31
    Notes:      profile is a special case and can't easily be constructed
                by iterating over list of gdac_vars as it must be updated
                with new data each profile.  Easier to have a stand-alone def
                to handle the few gdac vars like this...
    """
    logging.info('create_profile(%s): %d' % (platform, profile))
    seatrec_config = get_seatrec_config(platform)

    # Time all the same. Get first value, convert str to date and the reformat
    num_dim = (len(seatrec_xr.variables['z']))
    ts = seatrec_xr['time(UTC)'].values[0]
    ts = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
    timestamp = ts.strftime('%Y%m%dT%H%M%S')

    fname = '/data/gandalf/deployments/seatrec/%s-%s_rt.nc' % (platform, timestamp)
    seatrec_nc = Dataset(fname, "w", format="NETCDF4")
    seatrec_time = seatrec_nc.createDimension("time", num_dim)

    # Create vars
    create_global_variables(platform, seatrec_nc, seatrec_config)
    create_ARGO_variables(platform, seatrec_nc, seatrec_config)
    return seatrec_nc


def create_global_variables(platform, seatrec_nc, seatrec_config):
    """
    """
    logging.debug('create_global_variables(%s)', platform)

    date_created = (time.strftime('%Y-%m-%dT%H:%M:%SZ'))

    seatrec_nc.date_created = date_created
    seatrec_nc.date_issued = date_created
    seatrec_nc.date_modified = date_created


    #title_ts = time.strftime('%Y%m%dT%H%M%S', time.localtime(epoch))
    title = "%s-%s" % (platform, 0000000000)
    seatrec_nc.title = title
    seatrec_nc.id = title
    version = seatrec_config['global_attributes']['format_version']
    seatrec_nc.history = 'Created on %s using %s' % (date_created, version)
    seatrec_nc.PLATFORM_NUMBER = platform
    return seatrec_nc


def create_ARGO_variables(platform, dataset, seatrec_config):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-07-28
    Modified:   2023-04-05
    Notes:      Populates vars using config file values.
    """
    logging.debug('create_ARGO_variables(%s)', platform)
    for argo_var in seatrec_config['ARGO_variables']:
        logging.debug('create_seatrec_vars(): Creating var %s', argo_var)
        var_type = seatrec_config['ARGO_variables'][argo_var]['var_def']['var_type']
        var_fill = seatrec_config['ARGO_variables'][argo_var]['var_def']['var_fill']
        temp_name = dataset.createVariable(argo_var, var_type,
                                            fill_value=var_fill)

        """
        # QC vars must ref time, all others not...
        if '_qc' in gdac_var:
            temp_name = dataset.createVariable(gdac_var, var_type, ("time",),
                                               fill_value=var_fill)
        else:
            temp_name = dataset.createVariable(gdac_var, var_type,
                                                fill_value=var_fill)
        """
        for record in seatrec_config['ARGO_variables'][argo_var]['var_keys']:
            logging.debug('create_ARGO_variables(): adding %s to %s', record,
                          argo_var)
            value = seatrec_config['ARGO_variables'][argo_var]['var_keys'][record]
            if isinstance(value, str):
                #logging.info('STRING', argo_var, record, value)
                command = "temp_name.%s = '%s'" % (record, value)
                logging.debug("%s", command)
            else:
                #logging.info('NOT STRING', argo_var, record, value)
                command = "temp_name.%s = %d" % (record, value)
                logging.debug("%s", command)
            exec(command)
    return dataset


def get_seatrec_config(platform):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-06-22
    Modified:   2023-03-31
    Notes:      Gets all seatrec config info for creating nc files. Vars, etc.
                Added --config option for loading alternate config files
    """
    data_file = ("/data/gandalf/gandalf_configs/seatrec/seatrec_%s.json" %
                 platform)
    try:
        config = open(data_file, 'r').read()
    except FileNotFoundError as error:
        logging.warning('get_seatrec_config(%s): %s', platform, error)
        sys.exit()
    config = json.loads(config)
    gkeys = config['global_attributes'].keys()
    for gkey in gkeys:
        logging.debug("get_seatrec_config(%s): Global %s", platform, gkey)
    return config


def process_seatrec_data(platform_list):
    """ Kick it, yo. """

    logging.warning('process_seatrec_data(): %s', platform_list)
    seatrec_sensors = ['Temperature(C)', 'salinity(PSU)']
    features = []

    # Drop the first row as they put platform_id here
    for platform in platform_list:
        logging.warning('process_seatrec_data(%s)', platform)
        platform_profiles = get_platform_profiles(platform)[1:]

        # Only do this if we get good data...
        if platform_profiles:
            platform_df = profiles_to_df(platform_profiles)
            platform_df['z'] = platform_df['depth(m)']*-1

            # Create IOOS compliant NetCDF files for ERDDAP
            #gen_seatrec_profiles(platform, platform_df)
            # exit while testing

            logging.info("platform_df has %d rows" % len(platform_df))
            surface_marker = seatrec_surface_marker(platform, platform_df)
            features.append(surface_marker)
            last_profile = get_last_seatrec_profile(platform, platform_df)

            for sensor in seatrec_sensors:
                seatrec_plot_sensor(platform, platform_df, sensor)
                seatrec_plot_last_profile(platform, last_profile, sensor)
                plotly_seatrec_3D(platform, sensor, platform_df)

    return FeatureCollection(features)


def get_platform_ids():
    """
    Created:    2023-09-14
    Modified:   2023-10-28
    Author:     robertdcurrier@gmail.com
    Notes:      Gets list of all floats currently deployed from Seatrec
    """
    logging.warning(f'get_platform_ids(): Using {seatrec_root_url}')
    with urlopen(seatrec_root_url) as file:
        try:
            raw_html = file.read()
        except:
            logging.warning(f'get_platform_ids(): Failed to load url')
    platforms = bs4_parse(raw_html)
    logging.debug(f'get_platform_ids(): Got {platforms}')
    return (platforms)


def bs4_parse(raw_html):
    """
    Created:    2023-09-14
    Modified:   2023-10-28
    Author:     bob.currier@gcoos.org
    Notes:      Uses BeautifulSoup to parse html doc from url
    """
    platforms = []
    logging.debug(f'bs4_parse()')
    soup = BeautifulSoup(raw_html, 'html.parser')
       # Select all a tags
    fnames = soup.select('a')
    # look only for ts hrefs
    for fname in fnames:
        if '_ts' in str(fname):
            if 'seabio' not in str(fname):
                (id, ext) = str(fname.text).split('_')
                platforms.append(id)
    return platforms

def seatrec_process():
    """
    Created:    2023-02-25
    Modified:   2023-02-25
    Author:     robertdcurrier@gmail.com
    Notes:      Main entry point. We now plot both 2D and 3D seatrec data
    """
    register_matplotlib_converters()
    register_cmocean()
    #platforms = get_platform_ids()
    platforms = ['1249']

    if len(platforms) > 0:
        seatrec_fC = process_seatrec_data(platforms)
        write_geojson_file(seatrec_fC)


if __name__ == '__main__':
    # Need to add argparse so we can do singles without editing...
    logging.basicConfig(level=logging.INFO)
    start_time = time.time()
    seatrec_process()
    end_time = time.time()
    minutes = ((end_time - start_time) / 60)
    logging.warning('Duration: %0.2f minutes' % minutes)
