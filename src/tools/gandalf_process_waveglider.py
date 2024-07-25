#!/usr/bin/env python3
"""
Name:       gandalf_harvest_waveglider
Author:     bob.currier@gcoos.org
Created:    2017-09-23
Modified:   2021-08-24
Notes:      Waveglider harvesting routine for GANDALF.
            We use two CSV files as WG data has two URLs.
            One URL for science and one URL for vehicle

            2021-08-10 Request by SD to bring this back to GANDALF.
            Will be using sqlite vs PostGreSQL this time... and will
            take a page from Vela for most of the work.
"""
import requests
import datetime
import time
import sys
import os
import json
import datetime
import logging
import cmocean
import matplotlib
import calendar
import pandas as pd
import matplotlib.pyplot as plt
from  geojson import Feature, FeatureCollection, Point, LineString
from dateutil.parser import parse
from itertools import chain
from dateutil.parser import parse as date_parse



def register_cmocean():
    """Does what it says."""
    logging.info('register_cmocean()')
    plt.register_cmap(name='thermal', cmap=cmocean.cm.thermal)
    plt.register_cmap(name='haline', cmap=cmocean.cm.haline)
    plt.register_cmap(name='algae', cmap=cmocean.cm.algae)
    plt.register_cmap(name='matter', cmap=cmocean.cm.matter)
    plt.register_cmap(name='dense', cmap=cmocean.cm.dense)
    plt.register_cmap(name='oxy', cmap=cmocean.cm.oxy)
    plt.register_cmap(name='speed', cmap=cmocean.cm.speed)
    plt.register_cmap(name='tempo', cmap=cmocean.cm.tempo)
    plt.register_cmap(name='deep', cmap=cmocean.cm.deep)
    plt.register_cmap(name='solar', cmap=cmocean.cm.solar)
    plt.register_cmap(name='amp', cmap=cmocean.cm.amp)


def get_cmap(vehicle, sensor):
    """ Get cmocean color map for sensor from config file. """
    config = get_wg_config(vehicle)
    cm_name = config["cmaps"][sensor]
    return cm_name


def fetch_wg_data(vehicle):
    """
    Name:       fetch_data
    Author:     bob.currier@gcoos.org
    Created:    2017-09-25
    Modified:   2023-02-16
    Inputs:     URL for Liquid Robotics
    Outputs:    data
    Notes:      Single URL again as we remove excess in slim_df
    """
    config = get_wg_config(vehicle)
    user = config["system"]["user"]
    password = config["system"]["password"]
    kind_string = ""
    for kind in config["system"]["data_types"]:
        kind_string = kind_string + "%s," % kind
    start=config["system"]["data_start_datetime"]

    now = datetime.datetime.now()
    now = now.strftime("%Y-%m-%dT%H:%M:%S")
    url = config["system"]["data_url"] % (start, now, kind_string)
    msg = "fetch_wg_data(): %s" % url
    logging.info(msg)
    response = requests.get(url, auth=(user, password))
    return response.json()


def get_wg_config(vehicle):
    """ Get WaveGlider configuration data. """
    logging.debug('get_wg_config()')
    wg_cfile = '/data/gandalf/gandalf_configs/vehicles/%s/%s.cfg' % (vehicle, vehicle)
    try:
        with open(wg_cfile) as cfile:
            vehicle_config = json.loads(cfile.read())
        return vehicle_config
    except IOError as e:
        logging.warn('get_wg_config(): %s' % e)
    sys.exit()


def write_json(vehicle, json_data):
    """
    Name:       write_json()
    Author:     bob.currier@gcoos.org
    Created:    2017-09-24
    Modified:   2021-08-19
    Notes:      writes json data to file, D'oh! Now implemented for WG
    """
    logging.info("write_json()")
    config = get_wg_config(vehicle)
    outfile = config["system"]["json_file"]
    json_file = open(outfile, 'w')
    try:
        json_file.write(json.dumps(json_data))
        json_file.close()
        return
    except:
        logging.warning('write_json(): FAILED to write JSON output.')
        json_data.close()
        return

def get_nearest_n(epoch, df):
    """ Get Nearest Neighbor for use in getting closest epoch row to current
    CTD row when generating markers. CTD -> nn(WG), CTD -> nn(WX) etc. Returns
    the rows that matches so we can add heading, bearing and WX to marker.
    """
    logging.debug('get_nearest_n(): Finding %d' % epoch)
    for index, row in df.iterrows():
        if epoch < row['time']:
            continue
        else:
            return row


def gen_mashed_df(vehicle, df_list):
    """
    Created: 2021-08-27
    Takes multiple data frames, drops conflicting columns and combines to
    build a mash up that we can use to feed new_surf_markers
    """
    # We need these when building the data frames but not when concatenating
    # as they are dupliated across all three data frames
    mashed_rows = []
    # We will be dropping kind in make_wg_df and we can remove lat/lon from cfg
    drop_columns = ['kind', 'latitude', 'longitude']
    ctd_df = df_list[0]
    # This rename should pull columns from config file and not manually
    ctd_df.rename(columns={'temperature':'water_temperature'}, inplace=True)
    wx_df = df_list[1]
    wx_df.rename(columns={'temperature':'air_temperature'}, inplace=True)
    wx_df.rename(columns={'avgWindSpeed':'wind_speed'}, inplace=True)
    wg_df = df_list[2]
    waves_df = df_list[3]
    waves_df.rename(columns={'Hs':'wave_height'}, inplace=True)
    waves_df.rename(columns={'Dirp':'wave_direction'}, inplace=True)
    waves_df.rename(columns={'Fs':'wave_frequency'}, inplace=True)

    logging.info('gen_mashed_df(%s)' % vehicle)
    config = get_wg_config(vehicle)
    ctd_sensors = config["ctd_sensors"]
    # Here is where it all happens... CTD is the One Ring To Rule Them All
    start_time = time.time()

    for index, ctd_row in ctd_df.iterrows():
        # WX Sensors nearest row
        wx_row = get_nearest_n(ctd_row['time'], wx_df)
        # WG Sensors nearest row
        wg_row = get_nearest_n(ctd_row['time'], wg_df)
        # Waves Sensor nearest row
        waves_row = get_nearest_n(ctd_row['time'], waves_df)
        # Drop the conflicting time and index columns -- can't do this
        # prior as we need time to feed get_nearest_n Need to make this
        # iterable as we will be growing the list of data frames...
        # Do a for df in dfs:
        if wg_row is not None:
            wg_row.drop('time', inplace=True)
            wg_row.drop('index', inplace=True)
            wg_row.drop('kind', inplace=True)
        if wx_row is not None:
            wx_row.drop('time', inplace=True)
            wx_row.drop('index', inplace=True)
            wx_row.drop('kind', inplace=True)
        if waves_row is not None:
            waves_row.drop('time', inplace=True)
            waves_row.drop('index', inplace=True)
            waves_row.drop('kind', inplace=True)
        ctd_row.drop('index', inplace=True)
        if wg_row is not None and wx_row is not None and waves_row is not None:
            row_list = [ctd_row, wx_row, wg_row, waves_row]
            mash_row = pd.concat(row_list,axis=0, sort=False).fillna(0)
            mashed_rows.append(mash_row)
    mashed_df = pd.DataFrame(mashed_rows)
    end_time = time.time()
    seconds = (end_time - start_time)
    logging.info('gen_mashed_df(): runtime of %0.2f seconds' % seconds)
    return(mashed_df)


def new_surf_markers(vehicle, mashed_df):
    """
    Created: 2021-08-27
    Takes mashed_df and builds our surf_markers
    """
    markers = []
    config = get_wg_config(vehicle)
    public_name = config["system"]["public_name"]

    sensors = config["surf_marker_sensors"]
    currPosIcon = config["currPosIcon"]
    iconSize = config["iconSize"]
    for sensor in sensors:
        logging.info("new_surf_markers(%s): Processing %s" % (vehicle, sensor))
        cfgmin = config['sensor_settings'][sensor]['min']
        cfgmax = config['sensor_settings'][sensor]['max']
        smin = mashed_df[sensor].min()
        smax = mashed_df[sensor].max()
        range = smax-smin
        if range == 0:
            continue
        logging.info('new_surf_markers(): %s, %0.2f, %0.2f, %02f' %
                     (sensor, smin, smax, range))
        # Get color map here so we don't repeat for each record. 1X per sensor
        cmap_name = get_cmap(vehicle, sensor)
        cmap = matplotlib.cm.get_cmap(cmap_name)
        logging.info('new_surf_markers(): Using %s color map' % cmap_name)
        id = sensor
        format = '%Y-%m-%dT%H:%M:%S'
        deployment_date = config['system']["deployment_datetime"]
        deployment_epoch = int((time.mktime(time.strptime(
                            deployment_date,format))))
        logging.info('new_surf_markers(): Making markers')
        for index, row in mashed_df.iterrows():
            epoch = int(row['time'])
            epoch = int(epoch/1000)
            report_time = (datetime.datetime.fromtimestamp(epoch).
                             strftime("%Y-%m-%d %H:%MZ"))
            # Date math to calculate days_wet

            epoch_wet = (epoch - deployment_epoch)
            days_wet = int(epoch_wet/(86400))
            point = Point((row.longitude, row.latitude))

            surf_marker = Feature(geometry=point, id=sensor)
            cmap_scalar = 256/range
            cmap_index = int((row[sensor] - smin) * cmap_scalar)
            rgb = matplotlib.colors.to_hex(cmap(cmap_index))
            # Add properties here -- icon, color, size, etc
            # Otay, here's where we get tricky and use index for last pos
            surf_marker.properties['index'] = index
            surf_marker.properties['days_wet'] = days_wet
            surf_marker.properties['bearing'] = row['headingSub']
            surf_marker.properties['iconSize'] = iconSize
            surf_marker.properties['currPosIcon'] = currPosIcon
            surf_marker.properties['vehicle'] = vehicle
            surf_marker.properties['public_name'] = public_name
            surf_marker.properties['marker_color'] = rgb
            surf_marker.properties['fillColor'] = rgb
            surf_marker.properties['radius'] = (config["marker_settings"]
                                            ["radius"])
            surf_marker.properties['weight'] = (config["marker_settings"]
                                            ["weight"])
            surf_marker.properties['opacity'] = (config["marker_settings"]
                                             ["opacity"])
            surf_marker.properties['fillOpacity'] = (config["marker_settings"]
                                             ["fillOpacity"])
            # Vehicle html
            vehicle_html = """
            <center><img src='/static/images/waveglider_photo.png'></img></center>
            <center><span class='infoBoxHeading'>%s</span></center>
            <table class='infoBoxTable'>
            <tr><td class='wg_infoBoxSensor'>Date/Time:</td>
            <td class='wg_infoBoxData'>%s</td></tr>
            <tr><td class='wg_infoBoxSensor'>Position:</td>
            <td class='wg_infoBoxData'>%0.4fW/%0.4fN</td></tr>
            <tr><td class='wg_infoBoxSensor'>Heading:</td>
            <td class='wg_infoBoxData'>%0.2f degrees</td></tr>
            <tr><td class='wg_infoBoxSensor'>Speed:</td>
            <td class='wg_infoBoxData'>%0.2f knots</td></tr>
            <tr><td class='wg_infoBoxSensor'>Days Wet:</td>
            <td class='wg_infoBoxData'>%d</td></tr>
            </table>
            <hr>""" % (vehicle, report_time, row['longitude'],
                    row['latitude'], row['headingSub'], row['waterSpeed'],
                    days_wet)

            science_html = """
            <center><span class='infoBoxHeading'>Science</span></center>
            <table class='infoBoxTable'>"""
            for ib_sensor in sensors:
                s_row = ("""<tr><td class='wg_infoBoxSensor'>%s %s:
                </td><td class='wg_infoBoxData'>%0.2F</td></tr>""" %
                (config["sensor_settings"][ib_sensor]["public_name"],
                 config["sensor_settings"][ib_sensor]["units"],
                 row[ib_sensor]))
                science_html = science_html + s_row
            science_html = science_html + "</table>"
            if index == 0:
                layers_html = """
                <hr>
                <center><span class='infoBoxHeading'>Marker Layers</span></center>
                <table class='infoBoxTable'>"""
                for ib_sensor in sensors:
                    b_row = ("""
                            <table class='infoBoxTable'>
                            <tr><td class='wg_infoBoxSensor'>
                            <button class='wgButton' onclick=wgLayer(%s,'%s')>%s
                            </button></td></tr>
                            </table>
                            """ % (config["sensor_settings"][ib_sensor]
                                   ["layer_name"],
                                   config["sensor_settings"][ib_sensor]
                                   ["layer_image"],
                                   config["sensor_settings"][ib_sensor]
                                ["public_name"]))
                    layers_html = layers_html + b_row
            else:
                layers_html=""
            surf_marker.properties['html']  = (vehicle_html + science_html +
                                               layers_html)
            markers.append(surf_marker)
    return markers


def temporal_filter(vehicle, kind, df):
    """ Removes n rows to slim things down
        Modified 2021-08-26
    """
    config = get_wg_config(vehicle)
    num_rows = config['system']['num_rows']
    size = len(df)
    logging.info('temporal_filter(%s): data_frame has %d rows before pruning rows'
                  % (kind, size))
    df = df.iloc[::num_rows, :]
    size = len(df)
    logging.info('temporal_filter(%s): data_frame has %d rows after pruning rows'
                 % (kind, size))
    return df


def dedupe_pos(df):
    """ Deletes duplicate positions """
    size = len(df)
    logging.info('df(): data_frame has %d rows before dedupe' % size)
    df = df.drop_duplicates(subset=['longitude', 'latitude'])
    size = len(df)
    logging.info('df(): data_frame has %d rows after dedupe' % size)
    return df


def force_numeric(vehicle, df):
    """ Force convert all sensors to numeric as
    Data Portal encloses numbers in quotes... argh.
    Modified: 2021-08-27 updated time to be int vs float
    """
    logging.info('force_numeric(%s)' % vehicle)
    config = get_wg_config(vehicle)
    # CTD
    kind = df.iloc[0].kind

    ctd_sensors = config['ctd_sensors']
    wx_sensors = config['wx_sensors']
    wg_sensors = config['wg_sensors']
    waves_sensors = config['waves_sensors']
    # Toss kind as we don't want to force numeric on a string
    ctd_sensors.remove('kind')
    wx_sensors.remove('kind')
    wg_sensors.remove('kind')
    waves_sensors.remove('kind')

    if kind == 'CTD':
        sensors = ctd_sensors
        for sensor in sensors:
            logging.info('force_numeric(%s)' % sensor)
            if sensor != 'time':
                df[sensor] = df[sensor].astype(float)
            if sensor == 'time':
                df[sensor] = df[sensor].astype(int)

    if kind == 'Weather':
        sensors = wx_sensors
        for sensor in sensors:
            logging.info('force_numeric(%s)' % sensor)
            if sensor != 'time':
                df[sensor] = df[sensor].astype(float)
            if sensor == 'time':
                df[sensor] = df[sensor].astype(int)

    if kind == 'Waveglider':
        sensors = wg_sensors
        for sensor in sensors:
            logging.info('force_numeric(%s)' % sensor)
            if sensor != 'time':
                df[sensor] = df[sensor].astype(float)
            if sensor == 'time':
                df[sensor] = df[sensor].astype(int)

    if kind == 'Waves':
        sensors = waves_sensors
        for sensor in sensors:
            logging.info('force_numeric(%s)' % sensor)
            if sensor != 'time':
                df[sensor] = df[sensor].astype(float)
            if sensor == 'time':
                df[sensor] = df[sensor].astype(int)


    df = df.round(4)
    return(df)


def slim_df(vehicle, sensors, data_frame):
    """ Drop all but named columns
    Modified 2021-08-29
    """
    logging.info('slim_df(): Using %s and dropping excess' % sensors)
    slim_df = data_frame.filter(sensors, axis=1).reset_index()
    return slim_df


def wg_to_df(vehicle, data):
    """ Takes list of lists from WG API and makes CTD, WX and WG Dataframes"""
    logging.info("wg_to_df(): Transforming WG data to Dframes")
    ctd_data = []
    wx_data = []
    wg_data = []
    waves_data = []

    config = get_wg_config(vehicle)
    # Now we have list of lists
    for row in data:
        row = row[0]
        kind = (row['kind'])
        if kind == 'CTD':
            ctd_data.append(row)
        if kind == 'Weather':
            wx_data.append(row)
        if kind == 'Waveglider':
            wg_data.append(row)
        if kind == 'Waves':
            waves_data.append(row)

    ctd_df = pd.DataFrame(ctd_data)
    ctd_df = slim_df(vehicle, config["ctd_sensors"], ctd_df)
    ctd_df = ctd_df.sort_values(by=['time'], ascending=False)
    ctd_df = temporal_filter(vehicle, 'ctd', ctd_df)
    ctd_df = force_numeric(vehicle, ctd_df)

    wx_df = pd.DataFrame(wx_data)
    wx_df = slim_df(vehicle, config["wx_sensors"], wx_df)
    wx_df = wx_df.sort_values(by=['time'], ascending=False)
    wx_df = temporal_filter(vehicle, 'wx', wx_df)
    wx_df = force_numeric(vehicle, wx_df)

    wg_df = pd.DataFrame(wg_data)
    wg_df = slim_df(vehicle, config["wg_sensors"], wg_df)
    wg_df = wg_df.sort_values(by=['time'], ascending=False)
    wg_df = temporal_filter(vehicle, 'wg', wg_df)
    wg_df = force_numeric(vehicle, wg_df)

    waves_df = pd.DataFrame(waves_data)
    waves_df = slim_df(vehicle, config["waves_sensors"], waves_df)
    waves_df = waves_df.sort_values(by=['time'], ascending=False)
    waves_df = temporal_filter(vehicle, 'waves', waves_df)
    waves_df = force_numeric(vehicle, waves_df)

    df_list = [ctd_df, wx_df, wg_df, waves_df]
    return(df_list)


def create_wg_legends(vehicle, df):
    """
    Name:       create_legend
    Author:     robertdcurrier@gmail.com
    Created:    2021-01-19
    Modified:   2021-09-03
    Notes:      Takes name of sensor and df as input. Gets max
    value of db.sensor so we can set cmap range. Creates colorbar only
    and writes to /data/gandalf/deployments/legends for loading onto gandalfMap.
    """
    logging.info('create_wg_legends(%s)' % vehicle)
    config = get_wg_config(vehicle)

    # Set up the plots
    fig, ax = plt.subplots(figsize=(5, 1))
    fig.subplots_adjust(bottom=0.5)
    # Iterate over sensors

    for sensor in config['surf_marker_sensors']:
        # Set up the plots
        fig, ax = plt.subplots(figsize=(6, 1))
        fig.subplots_adjust(bottom=0.5)

        # min/max for sensors
        smin = df[sensor].min()
        if smin < config['sensor_settings'][sensor]['min']:
            logging.info("create_wg_legends(clipping %s from %0.4f to %0.4f" %
                         (sensor, smin, config['sensor_settings'][sensor]['min']))
            smin = config['sensor_settings'][sensor]['min']
        smax = df[sensor].max()
        if smax > config['sensor_settings'][sensor]['max']:
            logging.info("create_wg_legends(clipping %s from %0.4f to %0.4f" %
                         (sensor, smax, config['sensor_settings'][sensor]['max']))
            smax = config['sensor_settings'][sensor]['max']

        units = config['sensor_settings'][sensor]['units']
        public_name = config['sensor_settings'][sensor]['public_name']
        logging.info("create_wg_legends(%s, %s): min %0.4f max %0.4f" %
                     (vehicle, sensor, smin, smax))
        map_name = config['cmaps'][sensor]
        cmap = matplotlib.cm.get_cmap(map_name)
        logging.info("create_wg_legend(%s): Using %s" % (sensor, map_name))
        norm = matplotlib.colors.Normalize(vmin=smin, vmax=smax)
        label = "%s: %s %s" % (vehicle, public_name, units)
        fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap),
                     cax=ax, orientation='horizontal', label=label)
        plot_file = "%s/%s.png" % (config['wg_legend_dir'],
                               config['sensor_settings'][sensor]['layer_name'])
        logging.info('create_wg_legends(): Writing %s' % plot_file)
        plt.savefig(plot_file, dpi=100)
        plt.close(fig)


def gandalf_process_waveglider(vehicle):
    """
    Jump to the jam boogy woogy jam slam
    Modified: 2022-12-16
    Using a seperate df for each kind of data as variable names overlap
    """
    features = []
    logging.info("process_waveglider(%s): Intializing..." % vehicle)
    register_cmocean()
    config = get_wg_config(vehicle)

    data = fetch_wg_data(vehicle)
    df_list = wg_to_df(vehicle, data)
    mashed_df = gen_mashed_df(vehicle, df_list)
    create_wg_legends(vehicle, mashed_df)
    json_data = FeatureCollection(new_surf_markers(vehicle, mashed_df))
    write_json(vehicle, json_data)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    gandalf_process_waveglider('sv3-076')
