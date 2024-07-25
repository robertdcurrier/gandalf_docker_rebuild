#!/usr/bin/env python3
"""
Created:        2019-10-09
Modified:       2022-07-12
Author:         robertdcurrier@gmail.com
Pylint:         9.32 2022-07-12
Notes:          This app harvests data from Seaglider basestations
or their proxy using rsync, wget or ftp methods. If we have an account
on the dockserver we use rsync, if not, it's wget or ftp.
"""
import os
import sys
import logging
import argparse
from subprocess import Popen, PIPE
from ftplib import FTP
from gandalf_utils import get_vehicle_config
from gandalf_utils import get_deployed_seagliders
from gandalf_utils import get_deployment_status_all


def get_cli_args():
    """What it say.

    Author: robertdcurrier@gmail.com
    Created:    2018-11-06
    Modified:   2021-05-16
    """
    logging.info('get_cli_args()')
    arg_p = argparse.ArgumentParser()
    arg_p.add_argument("-v", "--vehicle", help="vehicle name",
                       nargs="?")
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

def use_wget(vehicle, v_config):
    """
    Name:       use_wget
    Created:    2022-07-12
    Modified:   2022-07-12
    Author:     bob.currier@gcoos.org
    Notes:      Uses config file settings and wget to get .nc files
    """
    # settings
    debug = bool(v_config['gandalf']['debug'])
    dockserver = v_config['gandalf']['dockserver']
    dockuser = v_config['gandalf']['dockuser']
    docklogpath = v_config['gandalf']['docklogpath']
    dockfrompath = v_config['gandalf']['dockfrompath']
    docklogfilter = v_config['gandalf']['docklogfilter']
    dockfromfilter = v_config['gandalf']['dockfromfilter']
    # nc files
    message = "use_wget(%s): Fetching sbd files" % vehicle
    logging.info(message)
    os.chdir()
    the_command = ("wget -v -r -l1 -nH --cut-dirs=3 %s/%s -A '%s.sbd'" %
                   (dockserver, dockfrompath, dockfromfilter))
    if debug:
        logging.info(the_command)
    the_pipe = Popen(the_command, shell=True, stdin=PIPE, stderr=PIPE)
    Popen.communicate(the_pipe)


def use_rsync(vehicle, v_config):
    """
    Name:       use_rsync
    Created:    2022-07-12
    Modified:   2022-07-12
    Author:     bob.currier@gcoos.org
    Notes:      Uses config file settings and subprocess to get .nc files
    """
    # settings
    dockserver = v_config['gandalf']['dockserver']
    dockuser = v_config['gandalf']['dockuser']
    dockpass = v_config['gandalf']['dockpass']
    dockport = v_config['gandalf']['dockport']
    dockfrompath = v_config['gandalf']['dockfrompath']
    dockfromfilter = v_config['gandalf']['dockfromfilter']
    deployed_data_dir = v_config['gandalf']['deployed_data_dir']
    ncdir = '%s/binary_files/nc' % v_config['gandalf']['deployed_data_dir']
    # nc files
    message = "use_rsync(%s): Fetching nc files" % vehicle
    logging.info(message)
    the_command = ("rsync -avp -e 'ssh -p %d' %s@%s:/%s/%s %s" %
                   (dockport, dockuser, dockserver, dockfrompath, dockfromfilter, ncdir))
    logging.info(the_command)
    the_pipe = Popen(the_command, shell=True, stdin=PIPE, stderr=PIPE)
    Popen.communicate(the_pipe)


def use_ftp(vehicle, v_config):
    """
    Name:       use_ftp
    Created:    2022-07-12
    Modified:   2022-07-12
    Author:     bob.currier@gcoos.org
    Notes:      Uses config file settings and ftplib to get .nc files
    """
    # settings
    dockserver = v_config['gandalf']['dockserver']
    dockuser = v_config['gandalf']['dockuser']
    dockpass = v_config['gandalf']['dockpass']
    dockfrompath = v_config['gandalf']['dockfrompath']
    dockfromfilter = v_config['gandalf']['dockfromfilter']
    deployed_data_dir = v_config['gandalf']['deployed_data_dir']
    ncdir = '%s/binary_files/nc' % deployed_data_dir
    message = 'use_ftp(%s): Using %s' % (vehicle, ncdir)
    logging.info(message)
    ftp = FTP(dockserver, user=dockuser, passwd=dockpass)
    ftp.cwd(dockfrompath)
    ncfiles = ftp.nlst(dockfromfilter)
    for filename in ncfiles:
        local_filename = os.path.join(ncdir, filename)
        file = open(local_filename, 'wb')
        message = 'use_ftp(%s): Fetching %s' % (vehicle, local_filename)
        logging.info(message)
        ftp.retrbinary('RETR '+ filename, file.write)
        file.close()
    ftp.quit()


def harvest_seaglider(vehicle):
    """
    Name:       harvest_seaglider
    Created:    2022-05-12
    Modified:   2022-07-12
    Author:     bob.currier@gcoos.org
    Notes:      Main entry point for harvester
    """
    message = "harvest_seaglider(%s)" % vehicle
    logging.info(message)
    v_config = get_vehicle_config(vehicle)
    if v_config['gandalf']['harvest_method'] == 'rsync':
        use_rsync(vehicle, v_config)
    if v_config['gandalf']['harvest_method'] == 'wget':
        pass
        #use_wget(vehicle, v_config)
    if v_config['gandalf']['harvest_method'] == 'ftp':
        use_ftp(vehicle, v_config)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    args = get_cli_args()
    seaglider = args['vehicle']
    if seaglider == None:
        SEAGLIDERS = get_deployed_seagliders(get_deployment_status_all())
        for seaglider in SEAGLIDERS:
            harvest_seaglider(seaglider)
    else:
        harvest_seaglider(seaglider)

