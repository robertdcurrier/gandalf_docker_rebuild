#!/usr/bin/env python3
"""
Name:       gandalf_cWorker_DIM.py
Created:    2023-05-23
Modified:   2023-05-23
Author:     bob.currier@gcoos.org
Inputs:     Vehicle data files in NetCDF format
Outputs:    GDAC-compliant NetCDF files with GANDALF expansion
Notes:      DIM for Hypoxia project with USM and Harris cWorker
"""
import sys
import os
import json
import logging
import time
import xarray
import glob
import argparse
import numpy as np
import pandas as pd
import datetime
import matplotlib
import cmocean
import matplotlib.pyplot as plt
import seawater as sw
from natsort import natsorted
from geojson import Feature, Point, FeatureCollection, LineString
from gandalf_utils import get_vehicle_config, flight_status
from gandalf_mongo import connect_mongo, insert_record



def get_cmap(vehicle, sensor):
    """ Get cmocean color map for sensor from config file. """
    config = get_vehicle_config(vehicle)
    cm_name = config['gandalf']["cmaps"][sensor]
    return cm_name


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


def read_netcdf(vehicle, nc_file):
    """
    Name:       read_netcdf
    Created:    2022-05-12
    Modified:   2022-05-17
    Author:     bob.currier@gcoos.org
    Notes:      Uses xarray to load vehicle-generated NetCDF files
    """
    df1 = []
    logging.debug('read_netcdf(%s, %s)' % (vehicle, nc_file))
    try:
        df1 = xarray.open_dataset(nc_file, decode_cf=True, mask_and_scale=True,
                                  decode_times=False)
        logging.debug("read_netcdf(%s): dims %s", vehicle, df1.dims)
    except:
        logging.warning("read_netcdf(%s, %s): Failed to open file.",
                        vehicle, nc_file)
    return df1


def validate_ds(sgfile, vehicle, sg_ds):
    """
    Author:     robertdcurrier@gmail.com
    Created:    2022-08-03
    Modified:   2022-08-03
    Notes:      Make sure all vars in config are in sg_ds. We've seen some
                corrupt files that are missing variables. For now we're just
                using ctd_depth... and we need to add validate_vars to the
                config file so we aren't hardwired here...
    """
    config = get_vehicle_config(vehicle)
    validate_vars = config['gandalf']['validate_vars']
    for var in validate_vars:
        logging.debug('validate_ds(): Checking for %s', var)
    if not var in sg_ds.variables:
        logging.warning('validate_ds(%s): %s failed validation for %s', vehicle,
                        sgfile, var)
        return False
    return True


def cw_qc_checks(vehicle, row):
    """
    """
    return True
    logging.debug('cw_qc_checks(%s)', vehicle)
    if(row['sea_water_practical_salinity_qartod_gross_range_test'] == 1):
        logging.debug(row['sea_water_practical_salinity'])
        logging.debug(row['sea_water_practical_salinity_qartod_gross_range_test'])
        qc = True
    else:
        logging.debug('cw_qc_checks(%s): Bad PSU', vehicle)
        return False

    if(row['sea_water_temperature_qartod_gross_range_test'] == 1):
        logging.debug(row['sea_water_temperature'])
        logging.debug(row['sea_water_temperature_qartod_gross_range_test'])
        qc = True
    else:
        logging.debug('cw_qc_checks(%s): Bad Temp', vehicle)
        return False

    if(row['volume_fraction_of_oxygen_in_sea_water_qartod_gross_range_test'] == 1):
        logging.debug(row['volume_fraction_of_oxygen_in_sea_water'])
        logging.debug(row['volume_fraction_of_oxygen_in_sea_water_qartod_gross_range_test'])
        qc = True
    else:
        logging.debug('cw_qc_checks(%s): Bad Oxy', vehicle)
        return False

    return qc


def cw_parse_files(vehicle, cw_files):
    """
    Name:       sg_parse_files
    Created:    2022-05-12
    Modified:   2023-06-14
    Author:     bob.currier@gcoos.org
    Notes:      Extracts select variables from xarray data, converting to
                pandas df then exporting to standard GANDALF sensors.csv file.
                This code is for standard SG deployments.
                Update: Added ValueError test so we don't barf if .nc files
                are corrupt. We just skip and continue.

                2023-06-16: FUCK ME!  I was making a new DF for each iteration over
                the files, adding them together, so we had 7,000+ entries. Now that
                we have fixed this we have 112. Was driving me CRAZY! No WONDER it was
                taking so long to spin through the files. FUCK! FUCK! FUCK!
    """
    logging.info('cw_parse_files(%s): Processing NetCDF files...' %
                 vehicle)

    config = get_vehicle_config(vehicle)
    client = connect_mongo()
    db = client.gandalf

    logging.info('cw_parse_files(%s): Purging %s', vehicle, vehicle)
    db[vehicle].drop()

    for ifile in cw_files:
        logging.info('cw_parse_files(%s): Parsing %s' % (vehicle, ifile))
        json_rows = []
        ds1 = []
        ds1 = read_netcdf(vehicle, ifile)
        df1 = ds1.to_dataframe()
        df1 = df1.round({'longitude': 2})
        df1 = df1.round({'latitude' : 2})
        df1 = df1.drop_duplicates(subset=['longitude', 'latitude'])

        df1['vehicle'] = vehicle

        for index, row in df1.iterrows():
            # Add time index to row for easy parsing in PD
            row['time'] = index

            # Need to update this as it isn't working with new data
            qc = cw_qc_checks(vehicle, row)
            if qc:
                ts = (datetime.datetime.fromtimestamp(index).
                      strftime("%Y-%m-%d %H:%M UTC"))
                row_js = json.loads(row.to_json())
                db[vehicle].insert_one(row_js)
    # Add close statement 2023-02-14
    client.close()


def get_cw_files(vehicle):
    """
    Name:       get_cw_files
    Created:    2022-05-12
    Modified:   2023-05-22
    Author:     bob.currier@gcoos.org
    Notes:      Get list of files in data dir.  Update: added status test
                for deployed/recovered
    """
    config = get_vehicle_config(vehicle)

    status = flight_status(vehicle)
    if status == 'deployed':
        data_dir = config['gandalf']['deployed_data_dir']
        nc_dir = config['gandalf']['deployed_nc_dir']
        plot_dir = config['gandalf']['plots']['deployed_plot_dir']
    if status == 'recovered':
        data_dir = config['gandalf']['post_data_dir_root']
        plot_dir = config['gandalf']['plots']['postprocess_plot_dir']

    nc_file_glob = nc_dir + '*.nc'
    logging.info('get_cw_files(%s): Using glob %s' %(vehicle, nc_file_glob))
    cw_files = natsorted(glob.glob(nc_file_glob))
    logging.info('get_cw_files(%s) found %d NetCDF files...' %
                 (vehicle, len(cw_files)))
    if len(cw_files) == 0:
        logging.warning("get_cw_files(%s): No files found. Skipping...", vehicle)
        return False
    return(cw_files)



def gandalf_cw_dim(vehicle):
    """
    Name:       gandalf_cw_dim
    Created:    2023-05-22
    Modified:   2023-05-22
    Author:     bob.currier@gcoos.org
    Notes:      Main entry point for Harris cWorker DIM
                Now iterating over all matched files after orphan test
    """
    smarkers = []
    logging.info('gandalf_cw_dim(%s)...' % vehicle)
    config = get_vehicle_config(vehicle)
    # Parse NetCDF and write MongoDB
    cw_files = get_cw_files(vehicle)
    if cw_files:
        cw_parse_files(vehicle, cw_files)


    # TO DO: SURF MARKERS ARE BEING A BITCH
    # GOT IT: Need to return a fC which we can then add to the primary FC so
    # it is feature (track) + feature (last_post) + FeatureCollection (surf_markers) = fC
    sm = cw_surf_markers(vehicle)
    track = gandalf_cw_track(vehicle)
    last_pos = gen_last_pos(vehicle)

    fC = FeatureCollection([track, last_pos, sm])
    write_geojson_file('cworker', fC)


def gen_df(vehicle):
    """
    Name:       gandalf_cw_track
    Author:     robertdcurrier@gmail.com
    Created:    2018-11-06
    Modified:   2023-06-14
    Notes:      Modified from SG code for use by SeaWorkers
    """

    try:
        client = connect_mongo()
    except:
        logging.warning('gen_df(): Failed to connect to MongoDB')
        sys.exit()

    db = client.gandalf
    numdocs = db[vehicle].count_documents({})

    logging.info('gen_df(%s): Found %d documents', vehicle, numdocs)
    results = (db[vehicle].find({}))
    df = pd.DataFrame(results)
    return df

def gandalf_cw_track(vehicle):
    """
    Name:       gandalf_cw_track
    Author:     robertdcurrier@gmail.com
    Created:    2018-11-06
    Modified:   2023-06-16
    Notes:      Modified for use with CWorker
    """
    logging.info('gandalf_cw_track(%s)' % vehicle)
    fcoll = []
    coords = []
    lats = []
    lons = []
    features = []

    # Pulling already slimmed data from Mongo
    df = gen_df(vehicle)

    config = get_vehicle_config(vehicle)
    public_name = config['gandalf']['public_name']
    operator = config['gandalf']['operator']
    vehicle_type = config['gandalf']['vehicle_type']
    project = config['gandalf']['project']

    idx = 0
    for lat in df['latitude']:
        lon = (df['longitude'].iloc[idx])
        idx+=1
        coords.append((lon, lat))
    logging.debug('gandalf_cw_track(%s): Finished iterating df', vehicle)
    logging.debug('gandalf_cw_track(%s): Making linestring', vehicle)

    track = LineString(coords)
    track = Feature(geometry=track, id='track')
    track.properties['style'] = (config['gandalf']['style'])

    return track


def gen_last_pos(vehicle):
    """
    Name:       gen_last_pos
    Author:     robertdcurrier@gmail.com
    Created:    2022-06-06
    Modified:   2023-06-16
    Notes:      Makes last pos html and icon for SeaWorker
    """
    logging.info('gen_last_pos(%s): generating last_pos', vehicle)

    # Pulling already slimmed data from Mongo
    df = gen_df(vehicle)

    config = get_vehicle_config(vehicle)
    vehicle = config['gandalf']['vehicle']
    # Date math to calculate days_wet
    deploy_date = (time.strftime("%Y-%m-%d",
                                 time.strptime(config["trajectory_datetime"],
                                                "%Y%m%dT%H%M")))
    date_obj = datetime.datetime.strptime(deploy_date, "%Y-%m-%d").date()
    current_date = datetime.date.today()
    days_wet = (current_date - date_obj).days
    infobox_image = config["gandalf"]["infoBoxImage"]
    public_name = config['gandalf']['public_name']
    operator = config['gandalf']['operator']
    vehicle_model = config['gandalf']['vehicle_model']
    project = config['gandalf']['project']
    data_source = config["gandalf"]["data_source"]
    last_lon = df.iloc[-1]['longitude'].round(4)
    last_lat = df.iloc[-1]['latitude'].round(4)
    last_pos = Point((last_lon, last_lat))
    teleport_zoom = config["gandalf"]["teleport_zoom"]


    epoch = df['time'].max()
    logging.info('gen_last_pos(%s): Got last epoch of %d',vehicle, epoch)
    last_surfaced = (datetime.datetime.fromtimestamp(epoch).
                     strftime("%Y-%m-%d %H:%M UTC"))
    logging.info('gen_last_pos(%s): Last Surface at %s',vehicle, last_surfaced)
    last_pos = Feature(geometry=last_pos, id='last_pos')
    last_pos.properties['vehicle'] = vehicle
    last_pos.properties['last_surfaced'] = last_surfaced

    last_pos.properties['latitude'] = last_lat
    last_pos.properties['longitude'] = last_lon
    last_pos.properties['teleport_zoom'] = teleport_zoom
    last_pos.properties['days_wet'] = days_wet
    last_pos.properties['public_name'] = public_name
    last_pos.properties['data_source'] = data_source
    last_pos.properties['style'] = (config['gandalf']['style'])
    last_pos.properties['currPosIcon'] = (config['gandalf']['currPosIcon'])
    last_pos.properties['iconSize'] = (config['gandalf']['iconSize'])
    # HTML for InfoBox
    last_pos.properties['html'] = """
    <div class='infoBoxTitle'><span class='infoBoxTitle'>%s</span></div>
    <center><img src=%s></img></center>
    <hr>
    <div class='infoBoxHeading'><span class='infoBoxHeading'>Status</span></div>
    <table class='infoBoxTable'>
    <tr>
        <td class='td_infoBoxSensor'>Last Report:</td>
        <td class='td_infoBoxData'>%s</td>
    </tr>
    <tr>
        <td class='td_infoBoxSensor'>Operator:</td>
        <td class='td_infoBoxData'>%s</td>
    </tr>

    <tr>
        <td class='td_infoBoxSensor'>Vehicle Type:</td>
        <td class='td_infoBoxData'>%s</td>
    </tr>

    <tr>
        <td class='td_infoBoxSensor'>Project:</td>
        <td class='td_infoBoxData'>%s</td>
    </tr>
    <tr>
        <td class='td_infoBoxSensor'>Last Position:</td>
        <td class='td_infoBoxData'>%sW %sN</td>
    </tr>
    <tr>
        <td class='td_infoBoxSensor'>Bearing:</td>
        <td class='td_infoBoxData'>%s degrees</td>
    </tr>
    <tr>
        <td class='td_infoBoxSensor'>Data Source:</td>
        <td class='td_infoBoxData'>%s</a>
        </td>
    </tr>
    </table>
    <div class = 'infoBoxBreakBar'>Science Plots</div>
    <div class = 'infoBoxPlotDiv'>
        <img class = 'infoBoxPlotImage'
            src = '/static/images/infoBox2DPlot.png'
            onclick="deployPlots('%s')">
        </img>
    </div>
    """ % (public_name, infobox_image, last_surfaced,
           operator, vehicle_model, project, last_lon, last_lat, 000,
           data_source, vehicle)

    # science_sensors
    sensors = config['gandalf']['plots']['plot_sensor_list']
    last_row = df.iloc[-1]

    science_header = """
              <div class = 'infoBoxBreakBar'>Science Data</div>
              <table class='infoBoxTable'>"""
    last_pos.properties['html'] = last_pos.properties['html'] + science_header
    for sensor in sensors:
        science_row = """<tr><td class='td_infoBoxSensor'>%s:
        </td><td>%0.2f</td></tr>"""  % (sensor, last_row[sensor])
        last_pos.properties['html'] =  last_pos.properties['html'] + science_row
    last_pos.properties['html'] = last_pos.properties['html'] + '</table>'
    return(last_pos)


def cw_surf_markers(vehicle):
    """
    Name:       cw_surf_markers
    Author:     robertdcurrier@gmail.com
    Created:    2020-05-26
    Modified:   2023-06-16
    Notes:      Borrowed from HALO and Navocean
                """
    markers = []
    logging.info('cw_surf_markers(%s)' % vehicle)
    point = Point((-99, 33))

    # Okay, FOR THE WIN!  We need to append and then make an fC.
    # We return the fC and then add to the list of objects being used
    # to create the final fC. Because we have a group of features
    # we have to create an fC and return that...

    # This is just a test stub. We'll need to rework main code
    # to reflect this. Hello, bitches!
    # pulling already slimmed data from Mongo
    df = gen_df(vehicle)

    config = get_vehicle_config(vehicle)
    sensors = config['gandalf']['plots']['plot_sensor_list']
    markers = []

    for index, row in df.iterrows():
        for sensor in sensors:
            logging.debug("cw_surf_markers(%s): Making layer for %s" % (vehicle,
                                                                sensor))
            # Get color map here so we don't repeat for each record. 1X per sensor
            cmap_name = get_cmap(vehicle, sensor)
            cmap = matplotlib.cm.get_cmap(cmap_name)
            logging.info('cw_surf_marker(%s): Using %s color map', sensor, cmap_name)

            cfgmin = config['gandalf']['sensor_ranges'][sensor]['min']
            cfgmax = config['gandalf']['sensor_ranges'][sensor]['max']
            smin = df[sensor].min()
            smax = df[sensor].max()
            range = smax-smin
            if range == 0:
                continue
            logging.debug("cw_surf_markers(%s): min %0.4f max %0.4f" % (sensor, smin,
                                                                 smax))
            sensor_marker = "%s_marker" % sensor
            point = Point((row['longitude'], row['latitude']))
            surf_marker = Feature(geometry=point, id=sensor_marker)
            surf_marker = Feature(geometry=point, id=sensor_marker)
            cmap_scalar = 256/range
            cmap_index = int((row[sensor] - smin) * cmap_scalar)
            rgb = matplotlib.colors.to_hex(cmap(cmap_index))
            # Add properties here -- icon, color, size, etc
            surf_marker.properties['marker_color'] = rgb
            surf_marker.properties['fillColor'] = rgb
            surf_marker.properties['radius'] = (config['gandalf']["marker_settings"]
                                                ["radius"])
            surf_marker.properties['weight'] = (config['gandalf']["marker_settings"]
                                                ["weight"])
            surf_marker.properties['opacity'] = (config['gandalf']["marker_settings"]
                                                 ["opacity"])
            surf_marker.properties['fillOpacity'] = (config['gandalf']["marker_settings"]
                                                 ["fillOpacity"])

            # Vehicle html
            surf_time = (datetime.datetime.fromtimestamp(row.time).
                             strftime("%Y-%m-%d %H:%M UTC"))
            surf_marker.properties['html'] = """
           <h5><center><span class='infoBoxHeading'>Status</span></center></h5>
               <table class='infoBoxTable'>
               <tr><td class='td_infoBoxSensor'>Vehicle:</td><td>%s</td></tr>
               <tr><td class='td_infoBoxSensor'>Date/Time:</td><td>%s</td></tr>
               <tr><td class='td_infoBoxSensor'>Position:</td><td>%0.4fW/%0.4fN</td></tr>
               <tr><td class='td_infoBoxSensor'>Heading:</td><td>%0.2f</td></tr>
               <tr><td class='td_infoBoxSensor'>Speed:</td><td>%0.2f knots</td></tr>
               </table>
               <hr>
               """ % (row.vehicle, surf_time, row.longitude, row.latitude, 0, 0)

            # science_sensors
            science_header = """
                      <h5><center><span class='infoBoxHeading'>Science</span></center></h5>
                      <table class='infoBoxTable'>"""
            surf_marker.properties['html'] = surf_marker.properties['html'] + science_header
            for sensor in sensors:
                science_row = """<tr><td class='td_infoBoxSensor'>%s:</td><td>%0.2f</td></tr>"""  % (sensor, row[sensor])
                surf_marker.properties['html'] =  surf_marker.properties['html'] + science_row
            surf_marker.properties['html'] =  surf_marker.properties['html'] + '</table>'
            markers.append(surf_marker)
    fC = (FeatureCollection(markers))
    return(fC)


def write_geojson_file(data_source, data):
    """
    Name:       write_geojson_file
    Author:     robertdcurrier@gmail.com
    Modified:   2020-05-26
    Notes:      Writes out geojson file for Jquery AJAX loading
    """
    logging.info("write_geojson_file(%s)" % data_source)
    fname = '/data/gandalf/deployments/geojson/%s.json' % data_source
    outf = open(fname, 'w')
    print(data, file=outf)
    outf.flush()
    outf.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    args = get_cli_args()
    register_cmocean()
    vehicle = args['vehicle']
    gandalf_cw_dim(vehicle)

