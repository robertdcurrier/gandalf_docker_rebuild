#!/usr/bin/env python3
"""Send nc files to GDAC.

FTPs .nc files from processed_dir/ngdac_files to
the glider DAC. Should be run just before midnight
and send files from that day. We can just do a
send all, but that gets messy after a vehicle
has been deployed for a few days. SO many profiles...

Modified: 2022-08-09
Notes:
    Integrating seagliders. Need to really clean this up
    and use all config file settings, not hardwired. Add
    argparse and move to -v vs argv[1]
"""
import os
import sys
import glob
import ftplib
import logging
from gandalf_utils import get_vehicle_config


def open_conn(config):
    """Open connection to the Glider DAC FTP server."""
    logging.info('open_conn(): Opening connection to GDAC')
    user = config["gandalf"]["gdac_user"]
    pw = config["gandalf"]["gdac_pw"]
    server = config["gandalf"]["gdac_server"]
    try:
        ftp = ftplib.FTP(server, user, pw)
    except ftplib.all_errors as e:
        logging.warning("open_conn(): Error %s" % e)
        sys.exit()
    return ftp


def get_nc_files(config):
    """Get list of all .nc files generated by gncutils."""
    logging.info("get_nc_files(%s)" % config['gandalf']['vehicle'])

    if config['gandalf']['vehicle_type'] == 'slocum':
        data_dir = ("%s/processed_data/ngdac_files/" %
                 config['gandalf']['deployed_data_dir'])

    if config['gandalf']['vehicle_type'] == 'seaglider':
        data_dir = ("%s/processed_data/nc_files" %
                    config['gandalf']['deployed_data_dir'])

    os.chdir(data_dir)
    nc_file_glob = ("*.nc")
    nc_file_names = sorted(glob.glob(nc_file_glob))
    return nc_file_names


def del_sent_files(sent_files, nc_files):
    """Compare nc_files to sent_files and remove sent files."""
    logging.debug("del_sent_files()")
    logging.debug("del_sent_files(): sent_files has %d file names" % len(sent_files))
    logging.debug("del_sent_files(): nc_files has %d file names" % len(nc_files))
    for file_name in sent_files:
        if file_name in nc_files:
            nc_files.remove(file_name)
    logging.info("del_sent_files(): returning %d file names to send" % len(nc_files))
    return nc_files


def get_sent_files(config):
    """Open list of sent files so we can drop dupes. List is updated."""
    logging.info("get_sent_files(%s)" % config['gandalf']['vehicle'])
    if config['gandalf']['vehicle_type'] == 'slocum':
        fname = ("%s/processed_data/ngdac_files/sentfiles.txt" %
                 config['gandalf']['deployed_data_dir'])

    if config['gandalf']['vehicle_type'] == 'seaglider':
        fname = ("%s/processed_data/nc_files/sentfiles.txt" %
                 config['gandalf']['deployed_data_dir'])
    try:
        # open for appending if not exist
        flist = open(fname, 'a+')
        # seek to beginning as a+ takes us to end
        flist.seek(0)
        flist = flist.read().splitlines()

    except IOError as e:
        logging.warning("get_sent_files(): Couldn't open sentfiles.txt. Error: %s" % e)
        sys.exit()
    return flist


def make_to_send_list(vehicle):
    """Figures out which files to send."""
    config = get_vehicle_config(vehicle)
    logging.info("make_to_send_list(%s)" % vehicle)
    ftp_send = bool(config['gandalf']['ftp_send'])
    logging.info('make_to_send_list(%s): ftp_send is %s' % (vehicle, ftp_send))
    sent_files = get_sent_files(config)
    nc_files = get_nc_files(config)
    to_send = del_sent_files(sent_files, nc_files)
    if(len(to_send) > 0):
        logging.warning('make_to_send_list(%s): %d files to send.' %
                     (vehicle, len(to_send)))
        send_files(vehicle, config, to_send)
    else:
        logging.warning("make_to_send_list(%s): No files to send." % vehicle)


def send_files(vehicle, config, to_send):
    """Put ftp files on the Glider DAC."""
    logging.info('ftp_send_files(%s)' % vehicle)
    if config['gandalf']['vehicle_type'] == 'slocum':
        dac_dir = ("%s/processed_data/ngdac_files" %
                   config['gandalf']['deployed_data_dir'])

    if config['gandalf']['vehicle_type'] == 'seaglider':
        dac_dir = ("%s/processed_data/nc_files" %
                   config['gandalf']['deployed_data_dir'])

    trajectory_name = config['trajectory_name']
    try:
        os.chdir(dac_dir)
    except ftplib.all_errors as e:
        logging.warning("ftp_send_files(): Error %s" % e)
        sys.exit()
    # Open sentfiles.txt
    logging.warning("ftp_send_files(%s)" % vehicle)
    fname = ("%s/sentfiles.txt" % dac_dir)
    try:
        flist = open(fname, 'a+')
    except IOError as e:
        logging.warning("send_files(): Couldn't open sentfiles.txt. Error: %s" % e)
        sys.exit()

    ftp_send = bool(config['gandalf']['ftp_send'])
    if ftp_send:
        if len(to_send) > 0:
            ftp = open_conn(config)
            try:
                ftp.cwd(trajectory_name)
            except ftplib.all_errors as e:
                logging.warning("send_files(): Error %s" % e)
            logging.debug("send_files(%s): Setting passive mode" % vehicle)
            ftp.set_pasv(True)

            for fname in to_send:
                fname = os.path.basename(fname)
                write_name = "%s\n" % fname
                fp = open(fname, 'rb')
                logging.warning("send_files(): sending %s" % fname)
                command = "STOR %s" % fname
                try:
                    ftp.storbinary(command, fp)
                    flist.write(write_name)
                except ftplib.all_errors as e:
                    logging.debug("send_files(): Error %s" % e)
            logging.warning("send_files(): Send complete for %s.\n" % vehicle)
    else:
        logging.info('gandalf_ftp_gdac(): FTP SEND DISABLED')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    if (len(sys.argv)) != 2:
        logging.warning("Usage: gandalf_ftp_gdac vehicle")
        sys.exit()
    make_to_send_list(sys.argv[1])