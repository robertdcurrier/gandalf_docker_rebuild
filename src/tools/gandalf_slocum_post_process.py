#!/usr/bin/python3
import sys
import itertools
import pandas as pd
import datetime
import time
import json
import geojson
import simplekml
import argparse
import logging
from gandalf_calc_sensors import calc_salinity, calc_density, calc_soundvel
from geojson import Feature, Point, FeatureCollection, LineString
from gandalf_slocum_plots_v2 import make_plots
from gandalf_utils import get_vehicle_config, flight_status
from gandalf_slocum_local import slocum_process_local, get_slocum_surfreps
from gandalf_slocum_binaries_v2 import process_binaries
import gandalf_slocum_plots_v2 as gsp
from gandalf_utils import dinkum_convert

"""
post-process.py: Simple script to post-process vehicle data.
gandalf_mcp runs on a timed loop, and rather than complicate
that code it was easier to write a tool specifically for
post-processing.
"""

def write_post_geojson(vehicle, data):
    """
    DOCSTRING
    """
    logging.info("write_post_geojson(%s)" % vehicle)
    config = get_vehicle_config(vehicle)
    dpath = (config['gandalf']['post_data_dir_root'])
    fname = ("%s/processed_data/%s.json" % (dpath, vehicle))
    logging.info("write_post_geojson(): Writing %s" % fname)
    outf = open(fname,'w')
    print(data, file=outf)
    outf.flush()
    outf.close()


def slocum_postprocess_track(vehicle):
    """
    Uses sensor.csv to generate track since we don't have log files
    The track can be used for the post-process map and KMZ files
    """
    logging.info('slocum_postprocess_track()...')
    features = []
    coords = []
    points = []
    # Lat/Lon ranges for qa/qc
    lon_min = -75
    lon_max = -100
    lat_min = 20
    lat_max = 37
    config = get_vehicle_config(vehicle)
    args = get_args()
    # Check to see if we just want to gen a KML file from command line
    if (args["kml"]):
        if args["input"] == None:
            logging.info('-i option required when using -k KML')
            sys.exit()
        logging.info('checking dstart and dend')
        if args["dstart"] == None or args["dend"] == None:
            logging.info('Must use -s dstart and -e dend args with -k  KML')
            sys.exit()
        logging.info("slocum_post_process_track(): Using %s " % args["input"])
        file_name = args["input"]
    else:
        # use config file options
        data_dir = config['gandalf']['post_data_dir_root']
        file_name = "%s/processed_data/sensors.csv" % (data_dir)
        logging.info("slocum_postprocess_track_(): Using %s " % file_name)

    data_frame = pd.read_csv(file_name)
    data_frame = data_frame.drop_duplicates(subset=('m_gps_lat', 'm_gps_lon'))

    if args["kml"]:
        data_start_date = int(time.mktime(time.strptime(args["dstart"],
                                                        '%Y%m%dT%H%M')))
        data_end_date = int(time.mktime(time.strptime(args["dend"],
                                                        '%Y%m%dT%H%M')))
    else:
        data_start_date = int(time.mktime(time.strptime(config['gandalf']
                                                        ['data_start_date'],
                                                        '%Y%m%dT%H%M')))
        data_end_date = int(time.mktime(time.strptime(config['gandalf']
                                                      ['data_end_date'],
                                                      '%Y%m%dT%H%M')))

    logging.info("Start Date: %s End Date: %s" % (data_start_date, data_end_date))
    for index, row in data_frame.iterrows():
        if (row['m_present_time']) != 'NaN':
             epoch = int(row['m_present_time'])
        if epoch > data_start_date and epoch < data_end_date:
            if pd.notna(row['m_gps_lat']):
                lon, lat = dinkum_convert(row['m_gps_lon'], row['m_gps_lat'])
                if (lon <lon_min and lon > lon_max and lat > lat_min and
                    lat < lat_max):
                        coords.append([float(lon), float(lat)])
        last_surfaced = (datetime.datetime.fromtimestamp(epoch).
                         strftime("%Y-%m-%d %H:%M UTC"))
    logging.info("slocum_postprocess_track(): %d coordinates" % len(coords))
    deduped = list(coords for coords,_ in itertools.groupby(coords))
    logging.info("slocum_postprocess_track: Deduped to %d coordinates" % len(deduped))
    for row in coords:
        point = Point((row[0], row[1]))
        points.append(point)
    # Track
    track = LineString(coords)
    track = Feature(geometry=track, id='track')
    track.properties['style'] = (config['gandalf']['style'])
    last_lon = points[-1]['coordinates'][0]
    last_lat = points[-1]['coordinates'][1]
    last_pos = Point((last_lon, last_lat))
    last_pos = Feature(geometry=last_pos, id='last_pos')
    last_pos.properties['style'] = (config['gandalf']['style'])
    last_pos.properties['currPosIcon'] = (config['gandalf']['currPosIcon'])
    last_pos.properties['wpIcon'] = (config['gandalf']['wpIcon'])
    last_pos.properties['iconSize'] = (config['gandalf']['iconSize'])
    last_pos.properties['last_surfaced'] = last_surfaced
    last_pos.properties['html'] = """
        <table class='infoBoxTable'>
        <tr><td class='td_infoBoxSensor'>Vehicle:</td><td>%s</td></tr>
        <tr><td class='td_infoBoxSensor'>Date/Time:</td><td>%s</td></tr>
        <tr><td class='td_infoBoxSensor'>Position:</td><td>%0.4fW/%0.4fN</td></tr>
        </table>
        """ % (config['gandalf']['public_name'], last_surfaced,
               last_lon, last_lat)
    features.append(track)
    features.append(last_pos)
    fC = FeatureCollection(features)
    logging.info('slocum_postprocess_track() returning fC')
    return(fC)


def slocum_post_kmz(vehicle):
    """
    For post-processing we use sensor.csv NOT logs as we don't always
    have access to older log files
    """
    logging.info('slocum_post_kmz(): using sensors.csv to generate KML')
    config = get_vehicle_config(vehicle)
    args = get_args()
    status = flight_status(vehicle)
    kml = simplekml.Kml()
    trackFc = slocum_postprocess_track(vehicle)
    for feature in trackFc['features']:
        if feature['id'] == 'track':
            coords = feature['geometry']['coordinates']
        if feature['id'] == 'last_pos':
            last_lat = feature['geometry']['coordinates'][1]
            last_lon = feature['geometry']['coordinates'][0]
            last_surfaced = feature['properties']['last_surfaced']
            balloon_text = """
            <![CDATA[
        	    <h2><b><center>%s Deployment End</center></b></h2><hr>
                    <table width=300>
                  	<tr>
                            <td><b>Coordinates:</td></b>
                            <td>%0.4fW %0.4fN</td>
                        </tr>
                        <tr>
        		    <td><b>Surfaced At:</td></b>
        		    <td>%s</td>
        		</tr>
        	    </table>
                ]]>""" % (vehicle, last_lon, last_lat, last_surfaced)

    the_track = kml.newlinestring(name=vehicle)
    the_track.coords = coords
    the_track.style.linestyle.width = 1
    the_track.style.linestyle.color = simplekml.Color.yellow

    # start pos
    start_pos = coords[0]
    logging.info("slocum_kmz(%s): Start Pos is %s" % (vehicle, start_pos))
    pnt = kml.newpoint()
    pnt.coords = [start_pos]
    pnt.style.iconstyle.scale = .5
    pnt.style.iconstyle.icon.href = 'https://gandalf.gcoos.org/static/images/green-icon.png'

    # end pos
    end_pos = (coords[-1])
    logging.info("slocum_kmz(%s): End Pos is %s" % (vehicle, end_pos))
    pnt = kml.newpoint()
    pnt.style.iconstyle.scale = 1
    pnt.coords = [end_pos]
    pnt.style.iconstyle.icon.href = 'https://gandalf.gcoos.org/static/images/slocum_stop.png'
    pnt.style.balloonstyle.text = balloon_text
    # write file
    config = get_vehicle_config(vehicle)
    status = flight_status(vehicle)
    # Deployed
    if status == 'deployed':
        kml_file = config['gandalf']['kml_file']
    # Post-Process
    if status == 'recovered':
        kml_file = config['gandalf']['post_kml_file']
    # Command line
    if args["input"]:
        if not args["output"]:
            logging.info("Using -i input requires -o output file name")
            sys.exit()
        else:
            kml_file = args["output"]

    logging.info("slocum_kmz(%s): writing %s" % (vehicle, kml_file))
    kml.save(kml_file)


def init_app():
    """
    Call everything from here so we avoid pylint
    grumbling about constants in __main__
    """
    args = get_args()
    vehicle = args["vehicle"]
    config = get_vehicle_config(vehicle)


    # Check to see if we just want to gen a KML file from command line
    if (args["kml"]):
        logging.info("Generating KML file only...")
        slocum_post_kmz(vehicle)
        sys.exit()

    # Not KML only so we proceed
    status = flight_status(vehicle)
    if status != 'recovered':
        logging.info("gandalf_slocum_post_process(): %s must be recovered!"
              %  vehicle)
        sys.exit()

    logging.info("%s is recovered. Proceeding..." % vehicle)
    config = get_vehicle_config(vehicle)
    # Binaries
    logging.info("Processing binaries for %s..." % vehicle)
    process_binaries(config, vehicle)
    # Calc sensors
    calc_salinity(config, vehicle)
    calc_density(config, vehicle)
    calc_soundvel(config, vehicle)


    logging.info("Generating track FC for %s" % vehicle)
    # Okay, we're going to generate the track from m_gps_lat/m_gps_lon
    # as we don't always have access to surface log files.
    trackFc = slocum_postprocess_track(vehicle)
    write_post_geojson(vehicle, trackFc)
    # KML
    logging.info("Generating KML for %s" % vehicle)
    slocum_post_kmz(vehicle)

    logging.info("Making plots for %s" % vehicle)
    gsp.make_plots(vehicle)

    logging.info("Postprocessing COMPLETE...")


def get_args():
    """
    Name: get_args
    Created: 2020-06-04
    Modified: 2020-07-02
    Author: robertdcurrier@gmail.com
    Notes: Gets command line args
    """
    arg_p = argparse.ArgumentParser()
    arg_p.add_argument("-k", "--kml",
                       help="Generate KML only", action="store_true")
    arg_p.add_argument("-s", "--dstart",
                       help="data start date")
    arg_p.add_argument("-e", "--dend",
                       help="data end date")
    arg_p.add_argument("-i", "--input",
                       help="Input path to sensors.csv")
    arg_p.add_argument("-o", "--output",
                       help="Output path for file write")
    arg_p.add_argument("-v", "--vehicle",
                       help="Platform number", required="True")
    args = vars(arg_p.parse_args())
    return args


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_time = time.time()
    init_app()
    end_time = time.time()
    minutes = ((end_time - start_time) / 60)
    logging.info('Duration: %0.2f minutes' % minutes)
