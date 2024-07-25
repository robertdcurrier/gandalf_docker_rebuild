#!/usr/bin/env python3
"""3D viz of glider data.

Author: robertdcurrier@gmail.com
Created: 2020-07-27
Modified: 2020-10-15
Notes: Trying out plotly. Probably a better fit...And it is a better fit.
Moved to production. Getting feedback from users.
Changed print() to logging.debug/info
"""
import sys
import json
import requests
import cmocean
import logging
import numpy as np
import pandas as pd
import seawater as sw
import plotly.express as px
import matplotlib.pyplot as plt
from decimal import getcontext, Decimal
from gandalf_utils import get_vehicle_config, get_sensor_config
from gandalf_utils import flight_status
from gandalf_slocum_plots_v2 import register_cmocean


def cmocean_to_plotly(cmap, pl_entries):
    """Convert cmocean color maps to Plotly colormaps.

    Author: robertdcurrier@gmail.com (via Plotly Docs)
    Created: 2020-08-18
    Modified: 2020-08-18
    Notes: Had to add list() as the docs were written for Python2
    """
    logging.info('cmocean_to_plotly(): Using %s as color map' % cmap.name)
    h = 1.0/(pl_entries-1)
    pl_colorscale = []

    for k in range(pl_entries):
        C = list(map(np.uint8, np.array(cmap(k*h)[:3])*255))
        pl_colorscale.append([k*h, 'rgb'+str((C[0], C[1], C[2]))])

    return pl_colorscale


def get_erddap_data(vehicle):
    """Name:       get_erddap_data.

    Author:     bob.currier@gcoos.org
    Created:    2020-07-30
    Modified:   2020-10-21
    Inputs:     vehicle_config
    Outputs:    erddap json data
    Notes:      We were fetching ERDDAP 3 times (track, plots, 3D) so we
    moved to one pull and write as text file for all further access
    """
    logging.info("get_erddap_data(%s)" % vehicle)
    config = get_vehicle_config(vehicle)
    #config = json.loads(open(vehicle_config,'r').read())
    json_dir = config["gandalf"]["gdac_json_dir"]
    json_file_name = ('%s/%s_gdac.json') % (json_dir, vehicle)
    # Need to check if file exists and bail if not
    logging.info('get_erddap_data(%s): Opening %s' % (vehicle, json_file_name))
    json_data = json.loads(open(json_file_name, 'r').read())
    return(json_data)


def dinkum_convert(dinkum_num):
    """Name:       dinkum_convert.

    Author:     bob.currier@gcoos.org
    Created:    2015-07-22
    Modified:   2015-07-22
    Inputs:     lon, lat in dddd.mm
    Outputs:    lon, lat in dd.ddd
    """
    getcontext().prec = 6
    dinkum_num = Decimal(dinkum_num)
    dinkum_int = int((dinkum_num / Decimal(100.0)))
    dddd = Decimal((dinkum_int + (dinkum_num - (dinkum_int * 100)) /
                    Decimal(60.0)))
    return float(dddd)


def create_df_erddap(vehicle, json_data):
    """Make DF from erddap data.

    Author:     bob.currier@gcoos.org
    Created:    2020-07-30
    Modified:   2030-07-30
    Outputs:    pandas df
    Notes: Borrowed from slocum erddap plots. Need to add gps columns for 3D
    """
    logging.info("create_df_erddap(%s)" % vehicle)
    v_config = get_vehicle_config(vehicle)
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

        depth = (feature['properties']['depth'])
        lat = (feature['geometry']['coordinates'][1])
        lon = (feature['geometry']['coordinates'][0])
        # We do the calc here so need to ensure no blanks
        if (temp and sal and press is not None):
            svel = sw.svel(temp, sal, press)
        else:
            svel = None
        sensor_vals.append([time, lon, lat, depth, temp, sal, density, sigma,
                            svel])
    # Create dataframe  -- calc_density will be changed to calc_sigma
    df = pd.DataFrame(sensor_vals, columns=["m_present_time",
                      "m_gps_lon", "m_gps_lat", "m_depth", "sci_water_temp",
                                            "calc_salinity", "calc_density",
                                            "calc_sigma", "calc_soundvel"])
    # Check for max_depth
    use_max_depth = v_config['gandalf']['plots']['use_max_plot_depth']
    max_depth = v_config['gandalf']['plots']['max_plot_depth']
    if use_max_depth:
        logging.debug('create_df_erddap(%s): Max depth is %s' % (vehicle, max_depth))
        df = df[df.m_depth < max_depth]
    # Invert depths
    df['m_depth'] = df['m_depth']*-1
    # Calc sigma
    return(df)


def create_df_slocum(vehicle):
    """Create df and clean it up.

    Author: robertdcurrier@gmail.com
    Created: 2020-07-29
    Modified: 2020-07-30
    Notes: Interpolate, convert m_gps to regular GPS, drop depth < 1
    """
    status = flight_status(vehicle)
    v_config = get_vehicle_config(vehicle)
    logging.debug('create_df_slocum(%s) is %s' % (vehicle, status))

    if status == 'deployed':
        data_file = v_config['gandalf']['deployed_sensors_csv']
    else:
        data_file = v_config['gandalf']['post_sensors_csv']
    logging.debug('create_df(%s): using %s' % (vehicle, data_file))

    df = pd.read_csv(data_file)
    df['m_gps_lon'] = (df['m_gps_lon'].interpolate(method='pad'))
    df['m_gps_lat'] = (df['m_gps_lat'].interpolate(method='pad'))

    # Could put a for sensor in sensors and interp here rather than plot

    # Drop any NaN GPS where interp couldn't fill in...
    df = df.dropna(subset=['m_gps_lat', 'm_gps_lon'])

    logging.debug("create_df(%s): df has initial length of %d" % (vehicle, len(df)))
    # Vectorize and use apply()
    logging.debug("create_df(): Converting Dinkum GPS coords")
    df['m_gps_lon'] = df['m_gps_lon'].apply(lambda x: dinkum_convert(x))
    df['m_gps_lat'] = df['m_gps_lat'].apply(lambda x: dinkum_convert(x))
    df['m_depth'] = df['sci_water_pressure'].apply(lambda x: x * 10)
    # No depth below 1
    df = df[df.m_depth > 1]
    # Check for max_depth
    use_max_depth = v_config['gandalf']['plots']['use_max_plot_depth']
    max_depth = v_config['gandalf']['plots']['max_plot_depth']
    if use_max_depth:
        logging.debug('create_df_slocum(%s): Max depth is %s' % (vehicle, max_depth))
        df = df[df.m_depth < max_depth]
    # Invert depths
    df['m_depth'] = df['m_depth']*-1
    logging.debug('create_df(): Returning DF of length %d' % len(df))
    return df


def set_color_lims(vehicle, sensor, df):
    """Configure colorbar min/max.

    Author: robertdcurrier@gmail.com
    Created: 2020-07-29
    Modified: 2020-07-29
    Notes: Gets sensor config settings and drops rows < min and > max
    """
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
    df = df[df[sensor] < (sensor_max + 1)]
    df = df[df[sensor] > (sensor_min - 1)]
    logging.debug("set_color_lims(): %s after adjustment has %0.4f min %0.4f max" %
          (sensor, df[sensor].min(), df[sensor].max()))
    return df


def get_cmocean_name(alt_colormap):
    """get_cmocean_name.

    Author: robertdcurrier@gmail.com
    Created: 2020-08-18
    Modified: 2020-08-18
    Notes: Crude mapping of cmocean names so we can use sensor.json string
    Need to make this a lookup table..although this does work...
    """
    logging.info('get_cmocean_name(%s)' % alt_colormap)
    if alt_colormap == 'oxygen':
        cmap = cmocean.cm.oxy
    if alt_colormap == 'thermal':
        cmap = cmocean.cm.thermal
    if alt_colormap == 'algae':
        cmap = cmocean.cm.algae
    if alt_colormap == 'matter':
        cmap = cmocean.cm.matter
    if alt_colormap == 'dense':
        cmap = cmocean.cm.dense
    if alt_colormap == 'speed':
        cmap = cmocean.cm.speed
    if alt_colormap == 'haline':
        cmap = cmocean.cm.haline
    if alt_colormap == 'turbid':
        cmap = cmocean.cm.turbid
    if alt_colormap == 'tempo':
        cmap = cmocean.cm.tempo
    if alt_colormap == 'jet':
        cmap = 'jet'
    return cmap


def make_fig(vehicle, sensor, sensor_df):
    """Fig for slocum with dinkum column names.

    Author:     bob.currier@gcoos.org
    Created:    2020-07-30
    Modified:   2020-07-30
    Notes: Working on migrating settings into config file
    """
    sensor_config = (get_sensor_config(vehicle))
    logging.debug('make_fig(%s, %s)' % (vehicle, sensor))
    # Convert cmocean colormap name to Plotly names
    for config in sensor_config:
        if (config['sensor'] == sensor):
            cm_name = get_cmocean_name(config['alt_colormap'])
            logging.info('make_fig(): cm_name is %s' % cm_name.name)
            if config['alt_colormap'] == 'matter':
                cmap = 'matter'
            else:
                cmap = cmocean_to_plotly(cm_name, len(sensor_df))

            logging.info('make_fig(%s): Using %s as colormap' %
                         (vehicle, config['alt_colormap']))

    logging.info('make_fig(): Getting colors for %s' % sensor)
    colors = sensor_df[sensor]
    fig = px.scatter_3d(sensor_df, y='m_gps_lat', x='m_gps_lon',
                        z='m_depth', color=colors, labels={
                            "m_gps_lat": "Lat",
                            "m_gps_lon": "Lon",
                            "m_depth": "Depth(m)"
                            }, height=900, color_continuous_scale=cmap)
    return fig


def plotly_scatter(vehicle, df):
    """Use Plotly to make our live scatter.

    Author:     bob.currier@gcoos.org
    Created:    2020-07-27
    Modified:   2020-07-29
    Notes: Working on migrating settings into config file
    """
    logging.info('plotly_scatter(%s)' % vehicle)
    status = flight_status(vehicle)
    v_config = get_vehicle_config(vehicle)
    sensors = v_config['gandalf']['plots']['plot_sensor_list']
    # Add code to pull in sensor name and units
    sensor_config = (get_sensor_config(vehicle))

    # Need to deNaN sensor and dedupe depth on a per-sensor basis
    for sensor in sensors:
        if "echodroid" in sensor:
            continue
        for config in sensor_config:
            if (config['sensor'] == sensor):
                plot_title = "%s %s" % (vehicle, (config['sensor_name']))
                logging.debug('make_fig(): Using %s as plot title' % plot_title)
        # We have to interpolate as we weren't getting enough data to plot
        # df[sensor] = (df[sensor].interpolate(method='pad'))
        logging.debug("plotly_scatter(%s): df has initial length of %d" %
                       (vehicle, len(df)))
        logging.debug('plotly_scatter(%s): Dropping %s duped depths...' %
                      (vehicle, sensor))
        sensor_df = df.drop_duplicates(subset=('m_depth', sensor))
        logging.debug("plotly_scatter(%s): sensor_df has length of %d" %
                      (vehicle, len(sensor_df)))
        sensor_df = set_color_lims(vehicle, sensor, sensor_df)
        logging.info('plotly_scatter(%s, %s)' % (vehicle, sensor))
        # Color map and height should be in config file
        fig = make_fig(vehicle, sensor, sensor_df)
        # marker_line_width and marker_size should be in config file
        fig.update_traces(mode='markers', marker_line_width=0, marker_size=4)
        # Tweak title font and size
        fig.update_layout(
                          title={'text': plot_title, 'y': 0.9, 'x': 0.5,
                                 'xanchor': 'center',
                                 'yanchor': 'top',
                                 'font_family': 'Times New Roman',
                                 'font_size': 24})
        # save it
        if status == 'deployed':
            plot_dir = v_config['gandalf']['plots']['deployed_plot_dir']
        else:
            plot_dir = v_config['gandalf']['plots']['postprocess_plot_dir']
        plot_file = "%s/%s3D.html" % (plot_dir, sensor)
        logging.info('plotly_scatter(%s): Saving %s' % (vehicle, plot_file))
        fig.write_html(plot_file)
        logging.debug("-------------------------------------------------------------")


def make_3D_plots(vehicle):
    """We kick it here.

    Author: robertdcurrier@gmail.com
    Created: 2020-07-27
    Modified: 2020-07-29
    Notes: This is where it all happens...
    """
    logging.info('make_3D_plots(%s)' % vehicle)
    v_config = get_vehicle_config(vehicle)
    v_type = v_config['gandalf']['vehicle_type']
    d_type = v_config['gandalf']['data_source']

    if 'Dockserver' in d_type:
        logging.debug('make_3D_plots(): Vehicle is type %s' % v_type)
        logging.debug('make_3D_plots(): Data for %s is %s' % (vehicle, d_type))
        df = create_df_slocum(vehicle)
        plotly_scatter(vehicle, df)

    if 'IOOS GDAC' in d_type:
        logging.debug('make_3D_plots(): Vehicle is type %s' % v_type)
        logging.debug('make_3D_plots(): Data for %s is %s' % (vehicle, d_type))
        json_data = get_erddap_data(vehicle)
        df = create_df_erddap(vehicle, json_data)
        plotly_scatter(vehicle, df)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    register_cmocean()
    if len(sys.argv) != 2:
        logging.warn('Usage: gandalf_3d_plotly.py vehicle')
        sys.exit()
    vehicle = sys.argv[1]
    make_3D_plots(vehicle)
