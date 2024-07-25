#!/usr/bin/env python3
"""
Name:       slocum2kml.py
Created:    2018-07-10
Modified:   2020-10-15
Author:     bob.currier@gcoos.org
Inputs:     ascii log files
Outputs:    kml file
pylint3:     9.67 2019-08-14

Notes:      Stand-alone KML generator created for Chad Lembke of USF.
            Changed fromm print() to logging.debug/warn
"""
import os
import sys
import glob
import time
import re
import datetime
import argparse
import simplekml
import math
import logging
from decimal import getcontext, Decimal
import pandas as pd
from gandalf_utils import get_vehicle_config, flight_status
from gandalf_utils import dinkum_convert
from natsort import natsorted


def get_log_files(config):
    """
    Name:       get_log_files()
    Author:     robertdcurrier@gmail.com
    Created:    2018-05-10
    Modified:   2020-04-22

    Gets slocum glider log files and parses for surfacing debugrmation.
    No good way to account for incomplete log files so we do a try/except
    for every parameter we want. I have yet to come up with a better way
    than the 'index + n' for the different params.
    """
    vehicle = config['gandalf']['vehicle']
    status = flight_status(vehicle)

    logging.debug('get_log_files(): %s is %s' % (vehicle, status))
    logging.debug('get_log_files(%s)' % vehicle)
    # 2019-07-25 added test for deployed or recovered

    # Deployed
    if status == 'deployed':
        log_dir = ("%s/ascii_files/logs") % config['gandalf']['deployed_data_dir']
    # Post-Process uses sensor.csv as we don't always have access to old logs
    if status == 'recovered':
        log_dir = ("%s/ascii_files/logs") % config['gandalf']['post_data_dir_root']

    file_names = glob.glob(log_dir + "/*.log")
    file_names = natsorted(file_names)

    active_files = []
    # Only use files > mission_start_time
    plot_start_date = int(time.mktime(time.strptime(config['trajectory_datetime'],
                                                    '%Y%m%dT%H%M')))
    if status == 'deployed':
        logging.debug("get_log_files(): Pruning files before Trajectory Start DateTime")
        for log_file in file_names:
            file_time = os.path.getmtime(log_file)
            if file_time > plot_start_date:
                active_files.append(log_file)
        return active_files

    if status == 'recovered':
        logging.debug("get_log_files(): NOT PRUNING FILES. YOU ARE ON YOUR OWN!")
        for log_file in file_names:
            file_time = os.path.getmtime(log_file)
            active_files.append(log_file)
        return active_files


def parse_log_files(config, log_files):
    """
    Reads log files, parses out surfacings and
    creates a data frame from said surfacings...
    This bitch is LONG with lots of variables so it will fail pylint big time.
    """
    vehicle = config['gandalf']['vehicle']
    logging.debug("parse_log_files(%s)" % vehicle)
    # REGEX patte:rns
    patt_curr_time = re.compile(
        r'(^Curr Time: )([A-Za-za-z].*20[0-9][0-9]+).*(MT.*[0-9]+)')
    patt_gps = re.compile(
        r'(^GPS Location:\s+)([0-9]+\.[0-9]+).*(-[0-9]+\.[0-9]+)')
    patt_mission_name = re.compile('(^MissionName:([A-Za-z0-9]+))')
    patt_because_why = re.compile(r'(^Because:([a-zA-Z]+.*)(\[))')
    patt_waypoint = re.compile(
        r'(^Waypoint: \(([0-9]+\.[0-9]+),(-[0-9]+\.[0-9]+).*)(Range: )([0-9]+).*(Bearing: )([0-9]+).*')
    surface_dialog = []
    surface_events = []
    # Preset these as we can't predict where Waypoint will appear
    because_why = "NaN"
    mission_name = "NaN"
    curr_time = "NaN"
    longitude = 0.0
    latitude = 0.0
    waypoint_lon = 0.0
    waypoint_lat = 0.0
    waypoint_range = 0.0
    waypoint_bearing = 0.0
    index = 0
    # Read 'em and weep
    for log_file in log_files:
        logging.debug("parsing %s" % log_file)
        data_file = open(log_file, encoding='utf-8')
        for line in data_file:
            surface_dialog.append(line.strip())
    # Suss out surfacings
    for line in surface_dialog:
        if "at surface" in line:
            try:
                because_why = surface_dialog[index + 1]
            except IndexError:
                logging.debug("Incomplete log file. No because_why. Breaking...")
                break
            # Because Why
            matchobj = patt_because_why.match(because_why)
            if matchobj:
                because_why = matchobj.group(2)
            # Mission Name
            try:
                mission_name = surface_dialog[index + 2]
            except IndexError:
                logging.debug("Incomplete log file. No mission_name. Breaking...")
                break

            matchobj = patt_mission_name.match(mission_name)
            if matchobj:
                mission_name = matchobj.group(2)
            else:
                mission_name = "NaN"
            # Current time
            try:
                matchobj = patt_curr_time.match(surface_dialog[index + 4])
                if matchobj:
                    curr_time = int(time.mktime(time.strptime(matchobj.group(2))))

            except IndexError:
                logging.debug("No current time data. Using last time value...")
                break

            # GPS location
            try:
                gps_loc = surface_dialog[index + 8]
            except IndexError:
                logging.debug("Incomplete log file. No gps_loc. Breaking...")
                break

            matchobj = patt_gps.match(gps_loc)
            if matchobj:
                latitude, longitude = dinkum_convert(matchobj.group(2),
                                                     matchobj.group(3))
            else:
                latitude = 0.0
                longitude = 0.0
            if curr_time != 'NaN':
                surface_events.append([because_why, mission_name, curr_time, longitude,
                                   latitude, waypoint_lon, waypoint_lat, waypoint_range,
                                   waypoint_bearing])
        # Waypoint
        matchobj = patt_waypoint.match(line)
        if matchobj:
            waypoint_lon, waypoint_lat = dinkum_convert(matchobj.group(3),
                                                        matchobj.group(2))
            waypoint_range = matchobj.group(5)
            waypoint_bearing = matchobj.group(7)

        index += 1
    # Need to add header for column names
    df = pd.DataFrame(surface_events, columns=('because_why','mission_name',
           'curr_time', 'longitude', 'latitude', 'waypoint_lon', 'waypoint_lat',
           'waypoint_range', 'waypoint_bearing'))
    # 2022-02-03 drop NaNs as we got a row with a NaN curr_time
    df.dropna(inplace=True)
    df = df.sort_values(by=['curr_time'])
    return df


def slocum_kmz(vehicle):
    """
    DOCSTRING
    """
    config = get_vehicle_config(vehicle)
    status = flight_status(vehicle)
    log_files = get_log_files(config)
    data_frame = parse_log_files(config, log_files)
    surfacings = []
    kml = simplekml.Kml()
    logging.debug('slocum_kmz(%s)' % vehicle)
    # Drop duplicate coords
    logging.debug("slocum_kmz(%s): Dropping dupe coords" % vehicle)
    data_frame = data_frame.drop_duplicates(subset=('longitude', 'latitude'))

    logging.debug("slocum_kmz(%s): building surfacing locations" % (vehicle))
    # Iterate over data frame
    if (len(data_frame) == 0):
        logging.warning('slocum_kmz(%s): No surfacings...', vehicle)
        return
    for _, row in data_frame.iterrows():
        isnan = math.isnan(float(row['curr_time']))
        if isnan:
            last_surfaced = 'NaN'
        else:
            last_surfaced = (datetime.datetime.fromtimestamp(row['curr_time']).
                         strftime("%Y-%m-%d %H:%M UTC"))
            logging.debug('slocum_kmz(): last_surfaced at %s' % last_surfaced)
        # We don't want any zero entries
        if(row['longitude'] and row['latitude'] != 0.0):
            coords = (float(row['longitude']), float(row['latitude']))
            pnt = kml.newpoint(name=last_surfaced)
            pnt.style.labelstyle.scale = 0  # no text
            surfacings.append(coords)
            pnt.coords = ([coords])

        # HTML for Surfacing InfoBoxes  -- we use balloonstyle.text to avoid
        # the annoying 'To From' direction links
        balloon_text = """
	<![CDATA[
	    <h2><b><center>%s</center></b></h2><hr>
            <table width=300>
          	<tr>
                    <td><b>Coordinates:</td></b>
                    <td>%0.4fW %0.4fN</td>
                </tr>
                <tr>
		    <td><b>Surfaced At:</td></b>
		    <td>%s</td>
		</tr>
		<tr>
                    <td><b>Because Why:</td></b>
                    <td>%s</td>
                </tr>
		<tr>
                    <td><b>Mission Name:</td></b>
                    <td>%s</td>
                </tr>
              	<tr>
                    <td><b>Waypoint:</b></td>
                    <td>%s Degrees at %s meters</td>
		<tr>
                </tr>
	    </table>
        ]]>
        """ % (vehicle, coords[0], coords[1], last_surfaced,
	              row['because_why'], row['mission_name'],
               row['waypoint_bearing'], row['waypoint_range'])

        pnt.style.balloonstyle.text = balloon_text
        pnt.style.labelstyle.color = simplekml.Color.red  # Make the text red
        # Use our small yellow circle here
        pnt.style.iconstyle.scale = .25
        pnt.style.iconstyle.icon.href = 'https://gandalf.gcoos.org/static/images/circle-yellow.png'

    # track
    the_track = kml.newlinestring(name=vehicle)
    the_track.coords = surfacings
    the_track.style.linestyle.width = 1
    the_track.style.linestyle.color = simplekml.Color.yellow

    # start pos
    start_pos = surfacings[0]
    logging.debug("slocum_kmz(%s): Start Pos is %s" % (vehicle, start_pos))
    pnt = kml.newpoint()
    pnt.coords = [start_pos]
    pnt.style.iconstyle.scale = .5
    pnt.style.iconstyle.icon.href = 'https://gandalf.gcoos.org/static/images/green-icon.png'

    # end pos
    end_pos = (surfacings[-1])
    logging.debug("slocum_kmz(%s): End Pos is %s" % (vehicle, end_pos))
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
    if len(sys.argv) == 3:
        kml_file = "%s/%s.kml" % (sys.argv[2], vehicle)

    logging.debug("slocum_kmz(%s): writing %s" % (vehicle, kml_file))
    kml.save(kml_file)



def init_app(vehicle, path):
    """
    Kick it
    """
    slocum_kmz(vehicle)



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # For command line usage
    if len(sys.argv) < 3:
        logging.warn('Usage: gandalf_slocum_to_kml vehicle path')
        sys.exit()
    else:
        logging.debug("gandalf_slocum_to_kml(): Manual mode...")
        vehicle = sys.argv[1]
    slocum_kmz(vehicle)
