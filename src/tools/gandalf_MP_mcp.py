#!/usr/bin/env python3
"""
Name:       gandalf_mcp.py
Created:    2016-09-05
Modified:   2022-06-01
Author:     bob.currier@gcoos.org
Inputs:     Dinkum binary files, ascii log files
Outputs:    GeoJSON Feature Collections, plots
Notes:      Master Control Program for GANDALF
pylint score: 10.0 out of 10.0 on 2018-06-05
Updated to use logging.info vs print() statements
"""
import json
import logging
import time
import sys
import multiprocessing as mp
from datetime import datetime
from geojson import FeatureCollection
from gandalf_process_gdac import gandalf_process_gdac
from gandalf_process_erddap import gandalf_process_erddap
from gandalf_slocum_local import get_slocum_surfreps
from gandalf_slocum_local import slocum_process_local, slocum_kmz
from gandalf_gdac_plots import gandalf_gdac_plots
from gandalf_ftp_gdac import make_to_send_list
from gandalf_slocum_plots_v2 import make_plots, register_cmocean
from gandalf_utils import get_vehicle_config
from gandalf_utils import get_deployed_slocum
from gandalf_utils import get_deployed_gdac
from gandalf_utils import get_deployed_seagliders
from gandalf_utils import get_deployed_saildrones
from gandalf_utils import get_deployment_status_all, flight_status

# New seaglider import
from gandalf_sg2gdac_DIM import gandalf_sg2gdac_DIM
from gandalf_sg_tracks_DIM import gandalf_sg_track
from gandalf_sg_PIM import gandalf_sg_plots
#
# Old seaglider imports -- Need to use this as new code doesn't yet write GEOJSON
#from gandalf_sg_DIM import gandalf_sg_dim
#
# Saildrone
from gandalf_sd_plots import gandalf_sd_plots
from gandalf_process_waveglider import gandalf_process_waveglider


def process_data_seaglider(vehicle_list):
    """
    Name:       process_data_seaglider
    Author:     robertdcurrier@gmail.com
    Created:    2022-05-19
    Modified:   2023-02-14
    Notes:      Uses gandalf_sg2csv to process SeaGlider data from BaseStations
                for which we have access privileges. Generates standard
                GANDALF sensors.csv file for use in plotting.
    """
    fColl = []

    logging.warning('process_data_seaglider(%s)' % vehicle_list)
    if len(vehicle_list) == 0:
        logging.info('No deployed seagliders')
        write_geojson_file('seagliders', fColl)
        return

    for vehicle in vehicle_list:
        # We moved plots here from 'Plots' section
        gandalf_sg2gdac_DIM(vehicle)
        sg_features = gandalf_sg_track(vehicle)
        if sg_features:
            fc = FeatureCollection(sg_features)
            fColl.append(fc)
            logging.info('(process_data_seaglider(): Writing Seaglider FeatureCollection')
            write_geojson_file('seagliders', fColl)
        else:
            logging.info("process_data_seaglider(): Empty Seaglider feature list.")
            fColl = []
            write_geojson_file('seagliders', fColl)


def process_local_gliders(vehicle_list):
    """
    Name:       process_local_gliders
    Author:     robertdcurrier@gmail.com
    Created:    2016-09-05
    Modified:   2020-06-01
    Notes:      Process vehicles for which we have access to sbd/tbd/log files
    2022-05-19: Need to check for new field in gandalf.cfg to determine
    vehicle type. If slocum, use slocum_process_local, if seaglider, we
    need new seaglider_process_local() function to handle.
    """
    # Process binaries and make kmz
    slocum_process_local(vehicle_list)
    # Surfacings and FC
    gandalf_local = get_slocum_surfreps(vehicle_list)
    return gandalf_local


def process_data_slocum(slocum_gliders):
    """
    processes binaries and surfreps
    """
    # Process data for all deployed local vehicles
    logging.warning("process_data_slocum(): %s" % slocum_gliders)
    local_features = process_local_gliders(slocum_gliders)
    if local_features:
        local_fc = json.dumps(local_features)
        write_geojson_file('local', local_fc)
    else:
        logging.info("process_data_slocum(): Empty LOCAL feature list.")
        local_fc = []
        write_geojson_file('local', local_fc)


def process_data_gdac(gdac_gliders):
    """
    Name:       process_data_gdac
    Author:     robertdcurrier@gmail.com
    Created:    2020-05-05
    Modified:   2022-06-14
    Notes:      Gets JSON from gdac and makes fc
    """
    features = []
    fColl = []

    for vehicle in gdac_gliders:
        logging.warning('process_data_gdac(%s)' % vehicle)
        gdac_features = gandalf_process_gdac(vehicle)
        for feature in gdac_features:
            features.append(feature)
    if features:
        fc = FeatureCollection(features)
        fColl.append(fc)
        logging.info('process_data_gdac(): Writing ERDDAP FeatureCollection')
        write_geojson_file('gdac', fColl)
    else:
        logging.info("process_data_gdac(): Empty ERDDAP feature list.")
        fColl = []
        write_geojson_file('gdac', fColl)


def process_data_erddap(erddap_vehicles):
    """
    Name:       process_data_erddap
    Author:     robertdcurrier@gmail.com
    Created:    2020-05-05
    Modified:   2022-08-22
    Notes:      Gets JSON from ERDDAP server and makes fc
    """
    features = []
    fColl = []

    for vehicle in erddap_vehicles:
        logging.warning('process_data_erddap(%s)' % vehicle)
        erddap_features = gandalf_process_erddap(vehicle)
        for feature in erddap_features:
            features.append(feature)
    if features:
        fc = FeatureCollection(features)
        fColl.append(fc)
        logging.info('process_data_erddap(): Writing ERDDAP FeatureCollection')
        write_geojson_file('erddap', fColl)
    else:
        logging.info("process_data_erddap(): Empty ERDDAP feature list.")
        fColl = []
        write_geojson_file('erddap', fColl)


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


def write_geojson_file(data_source, data):
    """
    Name:       write_geojson_file
    Modified:   2020-05-26
    Notes:      Writes out geojson file for Jquery AJAX loading
    """
    logging.warning("write_geojson_file(%s)" % data_source)
    fname = '/data/gandalf/deployments/geojson/%s.json' % data_source
    outf = open(fname, 'w')
    print(data, file=outf)
    outf.flush()
    outf.close()


def gandalf_mcp():
    """
    Name:       gandalf_mcp
    Author:     robertdcurrier@gmail.com
    Created:    2022-06-01
    Modified:   2023-02-14
    Notes:      Called by cron as external Docker exec
                2022-06-22: Working towards having only one set of config files
                and not using gandalf.cfg.   Status info is now in
                deployment.json for each vehicle, along with vehicle type.
                2023-02-14: Now using MongoDB for SG tracks, last_pos and plots
    """

    # DEPLOYMENT STATUS
    deployed = get_deployment_status_all()
    slocum_gliders = get_deployed_slocum(deployed)
    gdac_gliders = get_deployed_gdac(deployed)
    seagliders = get_deployed_seagliders(deployed)
    saildrones = get_deployed_saildrones(deployed)
    wavegliders = "sv3-076"

    logging.info("slocum: %s" % slocum_gliders)
    logging.info("seagliders: %s" % seagliders)
    logging.info("gdac: %s" %  gdac_gliders)
    logging.info("saildrones: %s" % saildrones)
    #logging.info("wavegliders: %s" % wavegliders)
    # PROCESS
    process_data_seaglider(seagliders)
    process_data_slocum(slocum_gliders)
    process_data_gdac(gdac_gliders)
    process_data_erddap(saildrones)
    #gandalf_process_waveglider(wavegliders)
    # PLOTS
    register_cmocean()
    for vehicle in seagliders:
        gandalf_sg_plots(vehicle)
    for vehicle in saildrones:
        gandalf_sd_plots(vehicle)
    for vehicle in slocum_gliders:
        make_plots(vehicle)
    for vehicle in gdac_gliders:
        gandalf_gdac_plots(vehicle)
    # Note: we can make this an 'all deployed' feature once we rewrite
    # gandalf_ftp_gdac to use all config file settings vs hardwired.
    # FTP Slocums
    for vehicle in slocum_gliders:
        logging.warning('gandalf_mcp(): Slocum FTP to GDAC for %s' % vehicle)
        config = get_vehicle_config(vehicle)
        if bool(config["gandalf"]["ftp_send"]):
            make_to_send_list(vehicle)
        else:
            logging.info("gandalf_mcp(%s): Not sending to Glider DAC" % vehicle)
    # FTP Seagliders
    for vehicle in seagliders:
        logging.warning('gandalf_mcp(): Seaglider FTP to GDAC for %s' % vehicle)
        config = get_vehicle_config(vehicle)
        if bool(config["gandalf"]["ftp_send"]):
            make_to_send_list(vehicle)
        else:
            logging.info("gandalf_mcp(%s): Not sending to Glider DAC" % vehicle)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_time = time.time()
    gandalf_mcp()
    end_time = time.time()
    minutes = ((end_time - start_time) / 60)
    logging.warning('Duration: %0.2f minutes' % minutes)
