#!/usr/bin/env python3
"""
Name:       gandalf_slocum_binaries_v2
Created:    2016-09-05
Modified:   2023-10-17
Author:     bob.currier@gcoos.org
Notes:      Processes sbd/dbd/tbd/ebd files and merges into merged.dba
            Changed from print() to logging.debug/debug
            2023-10-17: Began converting to MongoDB file names as per SG
"""
import sys
import os
import json
import glob
import time
import logging
import json
import pandas as pd
from subprocess import Popen, PIPE
from natsort import natsorted
from gandalf_utils import get_vehicle_config, flight_status
from gandalf_mongo import connect_mongo, insert_record
logging.basicConfig(level=logging.WARNING)


def prune_orphans(config, wayward_files, file_type):
    """
    Created:    2019-02-25
    Author:     bob.currier@gcoos.org
    Notes:      Removes mis-matched dbd/ebd or sbd/tbd files
                to allow for one-to-one merging
    """
    vehicle = config['gandalf']['vehicle']
    status = flight_status(vehicle)
    logging.info('prune_orphans()...')

    if status == 'deployed':
        root_dir = config['gandalf']['deployed_data_dir']
        data_dir = '%s/binary_files/%s/' % (root_dir, file_type)
    if status == 'recovered':
        root_dir = config['gandalf']['post_data_dir_root']
        data_dir = '%s/binary_files/%s' % (root_dir, file_type)
        logging.debug("prune_orphans(): Using %s" % data_dir)

    for the_file in wayward_files:
        file_name = "%s/%s.%s" % (data_dir, the_file, file_type)
        logging.debug("prune_orphans(): Pruning %s" % file_name)
        try:
            os.remove(file_name)
        except:
            logging.debug("Failed to remove %s" % file_name)
            sys.exit()


def find_orphans(config, flight_names, science_names):
    """
    Created:    2019-02-25
    Author:     bob.currier@gcoos.org
    Notes:      Finds mis-matched dbd/ebd or sbd/tbd files
                Returns flight names and science names
    """
    flight = []
    science = []
    vehicle = config['gandalf']['vehicle']
    status = flight_status(vehicle)
    logging.info('find_orphans()...')
    if status == 'deployed':
        flight_file_type = 'sbd'
        science_file_type = 'tbd'
    if status == 'recovered':
        flight_file_type = 'dbd'
        science_file_type = 'ebd'

    for the_file in flight_names:
        the_file = ((os.path.basename(the_file)))
        the_file = ((os.path.splitext(the_file)[0]))
        flight.append(the_file)

    for the_file in science_names:
        the_file = ((os.path.basename(the_file)))
        the_file = ((os.path.splitext(the_file)[0]))
        science.append(the_file)

    logging.debug("find_orphans(%s): %d flight, %d science" %
          (vehicle, len(flight_names), len(science_names)))

    # Flight file w/no corresponding science
    bad_flight = (set(flight) - set(science))
    if len(bad_flight) != 0:
        prune_orphans(config, bad_flight, flight_file_type)

    # Science file w/no corresponding flight
    bad_science = (set(science) - set(flight))
    if len(bad_science) != 0:
        prune_orphans(config, bad_science, science_file_type)
    else:
        logging.debug("find_orphans(%s): Flight and Science Match!" % vehicle)


def check_bd_mismatch(config, vehicle):
    """
    Created:    2019-02-25
    Author:     bob.currier@gcoos.org
    Notes:      Gets all *bd file names. File extension depends
                on deployment status.  Checks for mismatched
                lengths of flight and science. If mismatch sends
                file names to find_orphans()
    """
    status = flight_status(vehicle)
    logging.info("check_bd_mismatch(%s)" % vehicle)

    if status == 'deployed':
        root_dir = config['gandalf']['deployed_data_dir']
        flight_file_glob = root_dir + '/binary_files/sbd/*.sbd'
        science_file_glob = root_dir + '/binary_files/tbd/*.tbd'
    if status == 'recovered':
        root_dir = config['gandalf']['post_data_dir_root']
        flight_file_glob = root_dir + '/binary_files/dbd/*.dbd'
        science_file_glob = root_dir + '/binary_files/ebd/*.ebd'

    flight_bd_names = natsorted(glob.glob(flight_file_glob))
    science_bd_names = natsorted(glob.glob(science_file_glob))
    # We need to do this with file names, not length as we've run
    # into a bug wherein there are equal file numbers but still
    # mismatches in the names
    # 2023-09-23 Same bug showing with sedna. 133 sbd/tbd but name mismatch

    if (len(flight_bd_names) != len(science_bd_names)):
        # Find orphans, yo
        logging.warning("check_bd_mismatch(%s): Mismatch. Culling orphans." % vehicle)
        find_orphans(config, flight_bd_names, science_bd_names)
    else:
        logging.debug("check_bd_mismatch(%s): No orphans" % vehicle)


def parse_flight(config, vehicle, db):
    """
    Parses sbd/dbd files.
    NOTE: We changed from using glob of *.sbd/dbd as we would abort if
    an operator changed sbd sensors mid-mission. You can't use a * glob
    if the sbd header has changed. So -- we do a 'for each sbd/tbd' and
    write out 'n_flight.dba and n_science.dba file. These are then merged
    using merge_flight_science.
    2023-10-17: added 'db' to params
    """
    logging.warning('parse_flight(%s)' % vehicle)

    # Get flight status
    status = flight_status(vehicle)

    if status == 'deployed':
        dbd2asc = config['gandalf']['dbd2asc']
        dba_sensor_filter = config['gandalf']['dba_sensor_filter']
        root_dir = config['gandalf']['deployed_data_dir']
        data_dir = '%s/binary_files/sbd/' % root_dir
        file_glob = data_dir + '*.sbd'
        file_names = natsorted(glob.glob(file_glob))
        flight_sensor_list = " ".join(config['gandalf']['flight_sensor_list'])
    # Post-Process
    if status == 'recovered':
        dbd2asc = config['gandalf']['dbd2asc']
        dba_sensor_filter = config['gandalf']['dba_sensor_filter']
        root_dir = config['gandalf']['post_data_dir_root']
        data_dir = '%s/binary_files/dbd/' % root_dir
        file_glob = data_dir + '*.dbd'
        file_names = natsorted(glob.glob(file_glob))
        flight_sensor_list = " ".join(config['gandalf']
                                      ['postprocess_flight_sensor_list'])
    logging.debug( "parse_flight(): root_dir = %s" % root_dir)
    logging.debug( "parse_flight(): data_dir = %s" % data_dir)
    logging.debug( "parse_flight(): file_glob = %s" % file_glob)
    logging.debug( "parse_flight(): flight_sensor_list = %s" % flight_sensor_list)

    # Mongo doesn't like '-' in collection name
    collection = '%s_files' % vehicle.replace('-','_')
    old_files = []
    todo_files = []
    for doc in (db[collection].find({})):
        old_files.append(doc['filename'])

    for dinkum_file in file_names:
        if dinkum_file in old_files:
            logging.info('parse_flight(%s): Already processed %s', vehicle, dinkum_file)
        else:
            logging.warning('parse_flight(%s): new file %s', vehicle, dinkum_file )
            todo_files.append(dinkum_file)


    index = 0
    # Now we use MongoDB file names
    for dinkum_file in todo_files:
        the_file  = str.lower(os.path.split(dinkum_file)[1])
        the_file  = str.lower(os.path.splitext(the_file)[0])
        if status == 'deployed':
            dba_file = (('%s/processed_data/dba/flight/%s.dba') %
                            (root_dir, the_file))
        else:
            dba_file = (('%s/processed_data/dba/flight/%s.dba') %
                            (root_dir, the_file))
        dba_file = open(dba_file, 'wb', 0)
        the_command = ('%s %s | %s %s' %
                        (dbd2asc, dinkum_file, dba_sensor_filter,
                        flight_sensor_list))
        logging.info(("parse_flight(%s): running dbd2asc on %s") % (vehicle,
                                                                    dinkum_file))
        logging.debug(("parse_flight(): the_command = %s") % the_command)

        the_pipe = Popen(the_command, shell=True, stdin=PIPE,
                         stdout=dba_file, stderr=PIPE)
        Popen.wait(the_pipe)
        dba_file.close()

        # Write file name to MongoDB collection here
        fjson = '{"filename" : "%s"}' % dinkum_file
        db[collection].insert_one(json.loads(fjson))


def parse_science(config, vehicle, db):
    """
    Parses tbd/ebd files.
    NOTE: We changed from using glob of *.tbd/ebd as we would abort if
    an operator changed sbd sensors mid-mission. You can't use a * glob
    if the tbd header has changed. So -- we do a 'for each tbd/ebd' and
    write out 'n_flight.dba and n_science.dba file. These are then merged
    using merge_flight_science.
    2023-10-17: Added 'db' to params
    """
    logging.warning('parse_science(%s)' % vehicle)
    # Get flight status
    status = flight_status(vehicle)

    if status == 'deployed':
        dbd2asc = config['gandalf']['dbd2asc']
        dba_sensor_filter = config['gandalf']['dba_sensor_filter']
        root_dir = config['gandalf']['deployed_data_dir']
        data_dir = '%s/binary_files/tbd/' % root_dir
        file_glob = data_dir + '*.tbd'
        # Move to using TCL sort as getmtime sometimes fails
        file_names = natsorted(glob.glob(file_glob))
        science_sensor_list = " ".join(config['gandalf']['science_sensor_list'])

    # Post-Process
    if status == 'recovered':
        dbd2asc = config['gandalf']['dbd2asc']
        dba_sensor_filter = config['gandalf']['dba_sensor_filter']
        root_dir = config['gandalf']['post_data_dir_root']
        data_dir = '%s/binary_files/ebd/' % root_dir
        file_glob = data_dir + '*.ebd'
        file_names = natsorted(glob.glob(file_glob))
        science_dba = '%s/processed_data/science.dba' % (root_dir)
        science_sensor_list = " ".join(config['gandalf']
                                      ['postprocess_science_sensor_list'])

    logging.debug("parse_science(): root_dir = %s" % root_dir)
    logging.debug("parse_science(): data_dir = %s" % data_dir)
    logging.debug("parse_science(): file_glob = %s" % file_glob)
    logging.debug("parse_science(): science_sensor_list = %s" %
                 science_sensor_list)

    # Mongo doesn't like '-' in collection name
    collection = '%s_files' % vehicle.replace('-','_')
    old_files = []
    todo_files = []
    for doc in (db[collection].find({})):
        old_files.append(doc['filename'])

    for dinkum_file in file_names:
        if dinkum_file in old_files:
            logging.info('parse_science(%s): Already processed %s', vehicle, dinkum_file)
        else:
            logging.warning('parse_science(%s): new file %s', vehicle, dinkum_file )
            todo_files.append(dinkum_file)

    index = 0
    # Now we use MongoDB file names
    for dinkum_file in todo_files:
        the_file  = str.lower(os.path.split(dinkum_file)[1])
        the_file  = str.lower(os.path.splitext(the_file)[0])
        if status == 'deployed':
            dba_file = (('%s/processed_data/dba/science/%s.dba') %
                            (root_dir, the_file))
        else:
            dba_file = (('%s/processed_data/dba/science/%s.dba') %
                            (root_dir, the_file))
        dba_file = open(dba_file, 'wb', 0)
        the_command = ('%s %s | %s %s' %
                        (dbd2asc, dinkum_file, dba_sensor_filter,
                        science_sensor_list))
        logging.info(("parse_science(%s): running dbd2asc on %s") % (vehicle,
                                                                     dinkum_file))
        logging.debug(("parse_science(): the_command = %s") % the_command)

        the_pipe = Popen(the_command, shell=True, stdin=PIPE,
                         stdout=dba_file, stderr=PIPE)
        Popen.wait(the_pipe)
        dba_file.close()

        # Write file name to MongoDB collection here
        fjson = '{"filename" : "%s"}' % dinkum_file
        db[collection].insert_one(json.loads(fjson))


def merge_flight_science(config, vehicle, db):
    """
    Merges flight.dbas and science.dbas into merged.dba files
    2023-10-18 added db param so we can MDB the file names per sbd/tbd
    """
    logging.warning("merge_flight_science(%s)" % vehicle)
    status = flight_status(vehicle)
    dba_merge = config['gandalf']['dba_merge']

    # Mongo doesn't like '-' in collection name
    flight_collection = '%s_flight_dba_files' % vehicle.replace('-','_')
    science_collection = '%s_science_dba_files' % vehicle.replace('-','_')
    old_flight_files = []
    old_science_files = []
    todo_flight_files = []
    todo_science_files = []

    for doc in (db[flight_collection].find({})):
        old_flight_files.append(doc['filename'])

    for doc in (db[science_collection].find({})):
        old_science_files.append(doc['filename'])


    if status == 'deployed':
        root_dir = config['gandalf']['deployed_data_dir']
        flight_file_glob = root_dir + '/processed_data/dba/flight/*.dba'
        science_file_glob = root_dir + '/processed_data/dba/science/*.dba'
    if status == 'recovered':
        root_dir = config['gandalf']['post_data_dir_root']
        flight_file_glob = root_dir + '/processed_data/dba/flight/*.dba'
        science_file_glob = root_dir + '/processed_data/dba/science/*.dba'

    # Use natsort so we don't get a lexigraphical sort
    flight_dba_names =  natsorted(glob.glob(flight_file_glob))
    science_dba_names = natsorted(glob.glob(science_file_glob))

    """
    2023-10-18 Otay now the hard shit. We need to pull pairs from
    flight and science and do if in blah blah to build list as per
    parse_flight and parse_science. This is a bit trickier since we're
    dealing with matched pairs. Obvee we need to change the BOOYAH shat. :)
    """
    for fdb in flight_dba_names:
        if fdb in old_flight_files:
            logging.info(f'merge_flight_science(): {fdb} already merged')
        else:
            logging.warning(f'merge_flight_science({vehicle}): new file {fdb}')
            todo_flight_files.append(fdb)

    for sdb in science_dba_names:
        if sdb in old_science_files:
            logging.info(f'merge_flight_science(): {sdb} alrady merged')
        else:
            logging.warning(f'merge_flight_science({vehicle}): new file {sdb}')
            todo_science_files.append(sdb)

    # Merge matching pairs of flight.dba and science.dba unless none
    index = 0
    if(len(todo_flight_files) == 0) or (len(todo_science_files) == 0):
        logging.warning(f'merge_flight_science({vehicle}): No files to merge')
        return

    for flight_dba, science_dba in zip(todo_flight_files, todo_science_files):
        if os.path.basename(flight_dba) != os.path.basename(science_dba):
            logging.warning("merge_flight_science(): Mismatched DBA files. Skipping...")
            continue
        the_file  = str.lower(os.path.split(flight_dba)[1])
        the_file  = str.lower(os.path.splitext(the_file)[0])
        dba_file = (('%s/processed_data/dba/merged/%07d.dba') %
                    (root_dir, index))
        dba_file = open(dba_file, 'wb', 0)

        the_command = '%s %s %s' % (dba_merge, flight_dba, science_dba)
        logging.warning("merge_flight_science(): running dba_merge on %s, %s" %
                     (os.path.basename(flight_dba), os.path.basename(science_dba)))
        logging.debug(("the_command: %s") % the_command)

        the_pipe = Popen(the_command, shell=True, stdin=PIPE,
        stdout=dba_file, stderr=PIPE)
        Popen.wait(the_pipe)
        dba_file.close()
        index += 1
        # Write file names to MongoDB collection here
        fjson = '{"filename" : "%s"}' % (flight_dba)
        db[flight_collection].insert_one(json.loads(fjson))
        fjson = '{"filename" : "%s"}' % (science_dba)
        db[science_collection].insert_one(json.loads(fjson))



def pandas_gen_csv(config, vehicle):
    """
    Use Pandas to deal with DBA mess
    """
    status = flight_status(vehicle)
    logging.warning("pandas_gen_csv(%s)" % vehicle)

    if status == 'deployed':
        root_dir = config['gandalf']['deployed_data_dir']
        merged_file_glob = root_dir + '/processed_data/dba/merged/*.dba'
        merged_dba_names =  natsorted(glob.glob(merged_file_glob))

     # Post-Process
    if status == 'recovered':
        root_dir = config['gandalf']['post_data_dir_root']
        merged_file_glob = root_dir + '/processed_data/dba/merged/*.dba'
        merged_dba_names =  natsorted(glob.glob(merged_file_glob))

    for the_file in merged_dba_names:
        # Check for zero-length files
        if (os.path.getsize(the_file)) == 0:
            logging.debug("pandas_gen_csv(%s): Dropping zero length file %s" %
                  (vehicle, the_file))
            os.remove(the_file)
            merged_dba_names =  natsorted(glob.glob(merged_file_glob))
            #merged_dba_names.remove(the_file)
    try:
        df = pd.concat([pd.read_csv(f, sep=' ', header=14, skiprows=[15,16])
                        for f in merged_dba_names], sort=True)
    except:
        logging.warning(f'pandas_gen_csv({vehicle}): Failed to concat')
        return
    # Write it out
    csv_file = root_dir + '/processed_data/sensors.csv'
    logging.info("pandas_gen_csv(): Writing to sensors.csv")
    df.to_csv(csv_file, na_rep='NaN',index=False)


def pandas_gen_json(config, vehicle, db):
    """
    Use Pandas to create JSON for MDB -- need to only add data from new
    DBA files so we don't dupe
    """
    status = flight_status(vehicle)
    logging.warning("pandas_gen_json(%s)" % vehicle)
    vehicle = vehicle.replace('-','_')

    if status == 'deployed':
        root_dir = config['gandalf']['deployed_data_dir']
        merged_file_glob = root_dir + '/processed_data/dba/merged/*.dba'
        merged_dba_names =  natsorted(glob.glob(merged_file_glob))

     # Post-Process
    if status == 'recovered':
        root_dir = config['gandalf']['post_data_dir_root']
        merged_file_glob = root_dir + '/processed_data/dba/merged/*.dba'
        merged_dba_names =  natsorted(glob.glob(merged_file_glob))

    # Add the new file checks here just like in merge
    for the_file in merged_dba_names:
        # Check for zero-length files
        if (os.path.getsize(the_file)) == 0:
            logging.debug("pandas_gen_json(%s): Dropping zero length file %s" %
                  (vehicle, the_file))
            os.remove(the_file)
            merged_dba_names =  natsorted(glob.glob(merged_file_glob))
            #merged_dba_names.remove(the_file)
    try:
        df = pd.concat([pd.read_csv(f, sep=' ', header=14, skiprows=[15,16])
                        for f in merged_dba_names], sort=True)
        logging.warning(f'pandas_gen_csv({vehicle}): Succesfully created DF')
        slocum_json = json.loads(df.to_json(orient='records'))
        try:
            db[vehicle].insert_many(slocum_json)
        except:
            logging.warning(f'pandas_gen_json({vehicle}): Insert failed')

    except:
        logging.warning(f'pandas_gen_json({vehicle}): Failed to concat')
        return



def clean_dba_files(config, vehicle):
    """
    Wipes all dba files before we start the run
    """
    status = flight_status(vehicle)
    logging.info("clean_dba_files(%s)" % vehicle)

    if status == 'deployed':
        logging.debug('clean_dba_files(%s): removing old flight dba files' % vehicle)
        dpath = (config['gandalf']['deployed_data_dir'] +
                 '/processed_data/dba/flight/*.dba')
    else:
        dpath = (config['gandalf']['post_data_dir_root'] +
                 '/processed_data/dba/flight/*.dba')
    dfiles = glob.glob(dpath)
    for dba_file in dfiles:
        os.remove(dba_file)
    logging.debug('clean_dba_files(%s): removing old science dba files' % vehicle)
    if status == 'deployed':
        dpath = (config['gandalf']['deployed_data_dir'] +
                 '/processed_data/dba/science/*.dba')
    else:
        dpath = (config['gandalf']['post_data_dir_root'] +
                 '/processed_data/dba/science/*.dba')
    dfiles = glob.glob(dpath)
    for dba_file in dfiles:
        os.remove(dba_file)
    logging.debug('clean_dba_files(%s): removing old merged dba files' % vehicle)
    if status == 'deployed':
        dpath = (config['gandalf']['deployed_data_dir'] +
                 '/processed_data/dba/merged/*.dba')
    else:
        dpath = (config['gandalf']['post_data_dir_root'] +
                 '/processed_data/dba/merged/*.dba')
    dfiles = glob.glob(dpath)
    for dba_file in dfiles:
        os.remove(dba_file)


def wipe_old_bd(config, vehicle):
    """
    Removes all s/dbd and t/ebd files
    from prior to mission start. Some
    operators are slobs and don't clean up
    their from-glider folders after each
    deployment.
    """
    logging.info("wipe_old_bd(%s)" % vehicle)
    status = flight_status(vehicle)
    # Only use files > mission_start_time
    plot_start_date = int(time.mktime(time.strptime(config['gandalf']
                                                    ['data_start_date'],
                                                    '%Y%m%dT%H%M')))
    files_removed = 0
    if status == 'deployed':
        root_dir = config['gandalf']['deployed_data_dir']
        flight_data_dir = '%s/binary_files/sbd/' % root_dir
        flight_file_glob = flight_data_dir + '*.sbd'
        flight_file_names = natsorted(glob.glob(flight_file_glob))
        science_data_dir = '%s/binary_files/tbd/' % root_dir
        science_file_glob = science_data_dir + '*.tbd'
        science_file_names = natsorted(glob.glob(science_file_glob))

    if status == 'recovered':
        root_dir = config['gandalf']['post_data_dir_root']
        flight_data_dir = '%s/binary_files/dbd/' % root_dir
        flight_file_glob = flight_data_dir + '*.dbd'
        flight_file_names = natsorted(glob.glob(flight_file_glob))
        science_data_dir = '%s/binary_files/ebd/' % root_dir
        science_file_glob = science_data_dir + '*.ebd'
        science_file_names = natsorted(glob.glob(science_file_glob))

    # sbd/dbd
    for bd_file in flight_file_names:
        file_time = os.path.getmtime(bd_file)
        # have to compare like to like here...
        if file_time < plot_start_date:
            logging.debug("wipe_old_bd(%s): Removing %s" % (vehicle, bd_file))
            os.remove(bd_file)
            files_removed += 1
    # tbd/ebd
    for bd_file in science_file_names:
        file_time = os.path.getmtime(bd_file)
        if file_time < plot_start_date:
            logging.debug("wipe_old_bd(%s): Removing %s" % (vehicle, bd_file))
            os.remove(bd_file)
            files_removed += 1
    logging.debug("wipe_old_bd(%s): Removed %d files" % (vehicle, files_removed))


def process_binaries(config, vehicle):
    """
    Main function.
    """
    logging.info("process_binaries(%s)" % vehicle)
    # Fire up a mdb conn
    client = connect_mongo()
    db = client.gandalf

    wipe_old_bd(config, vehicle)
    check_bd_mismatch(config, vehicle)
    parse_flight(config, vehicle, db)
    parse_science(config, vehicle, db)
    merge_flight_science(config, vehicle, db)
    pandas_gen_csv(config, vehicle)
    #pandas_gen_json(config, vehicle, db)


if __name__ == '__main__':
    if len(sys.argv) != 2:
            logging.warning('usage: gaandalf_slocum_binaries vehicle')
            sys.exit()
    config = get_vehicle_config(sys.argv[1])
    process_binaries(config, sys.argv[1])
