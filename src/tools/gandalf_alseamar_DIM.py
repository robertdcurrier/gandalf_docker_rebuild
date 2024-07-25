#!/usr/bin/env python3
"""3D viz of glider and seatrec data.

Author: 	robertdcurrier@gmail.com
Created: 	2023-02-21
Modified: 	2023-03-06
Notes: 		Started work. Will be using MongoDB per other DIMs.
			Alseamar has two file types: gli, which is like an sbd (flight),
			and pld1, which is the equivalent of a tbd (science) file.
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
import glob
import multiprocessing as mp
import numpy as np
import pandas as pd
import seawater as sw
from datetime import datetime
from calendar import timegm
from matplotlib import dates as mpd
from matplotlib import pyplot as plt
from matplotlib import colors as colors
from matplotlib import cm as cm
from decimal import getcontext, Decimal
from geojson import LineString, FeatureCollection, Feature, Point
from pandas.plotting import register_matplotlib_converters
from natsort import natsorted
from gandalf_utils import get_vehicle_config, get_sensor_config, flight_status
from gandalf_mongo import connect_mongo, insert_record


def get_sensor_plot_range(vehicle, sensor):
    """
    Gets plot range for each sensor so we don't overshoot."""
    logging.info("get_sensor_plot_range(%s, %s)" % (vehicle, sensor))
    sensors = get_sensor_config(vehicle)
    for record in sensors:
        if record['sensor'] == sensor:
            sensor_plot_min = float(record['sensor_plot_min'])
            sensor_plot_max = float(record['sensor_plot_max'])
            return (sensor_plot_min, sensor_plot_max)


def register_cmocean():
    """Does what it says."""
    plt.register_cmap(name='thermal', cmap=cmocean.cm.thermal)
    plt.register_cmap(name='haline', cmap=cmocean.cm.haline)
    plt.register_cmap(name='algae', cmap=cmocean.cm.algae)
    plt.register_cmap(name='matter', cmap=cmocean.cm.matter)
    plt.register_cmap(name='dense', cmap=cmocean.cm.dense)
    plt.register_cmap(name='oxygen', cmap=cmocean.cm.oxy)
    plt.register_cmap(name='speed', cmap=cmocean.cm.speed)
    plt.register_cmap(name='turbid', cmap=cmocean.cm.turbid)
    plt.register_cmap(name='tempo', cmap=cmocean.cm.turbid)


def config_date_axis(config, vehicle):
    """
    Sets up our style
    """
    logging.debug("config_date_axis(): Setting x axis for date/time display")
    # instantiate the plot
    fig = plt.figure(figsize=(14, 6))
    gca = plt.gca()
    # make room for xlabel
    plt.subplots_adjust(bottom=0.15)
    # labels
    plt.ylabel('Depth (m)')
    # ticks
    """
    Sets up date/time x axis
    Modified: 2020-05-19
    """
    # hours = mpd.HourLocator(interval = 6)
    gca.xaxis.set_tick_params(which='major')
    plt.setp(gca.xaxis.get_majorticklabels(), rotation=45, fontsize=6)
    major_formatter = mpd.DateFormatter('%m/%d')
    # gca.xaxis.set_major_locator(hours)
    gca.xaxis.set_major_formatter(major_formatter)
    gca.set_xlabel('Date', fontsize=12)

    return fig


def normalize_sensor_range(sensor, vehicle, data_frame):
    """ Set sane sensor ranges."""
    sensor_min = np.nanmin(data_frame[sensor])
    sensor_max = np.nanmax(data_frame[sensor])
    sensor_plot_min, sensor_plot_max = get_sensor_plot_range(vehicle, sensor)
    logging.info("normalize_sensor_range(%s): %0.4f min, %0.4f max readings" %
          (sensor, sensor_min, sensor_max))
    if sensor_min < sensor_plot_min:
        logging.info ("normalize_sensor_range(%s): adjusting min %0.4f to %0.4f" %
               (sensor, sensor_min, sensor_plot_min))
        sensor_min = float(sensor_plot_min)
    if sensor_max > sensor_plot_max:
        logging.info ("normalize_sensor_range(%s): adjusting max %0.4f to %0.4f" %
               (sensor, sensor_max, sensor_plot_max))
        sensor_max = float(sensor_plot_max)
    logging.info("normalize_sensor_range(%s): Plotting with %0.4f MIN and %0.4f MAX" %
          (sensor, sensor_min, sensor_max))
    return(sensor_min, sensor_max)


def get_alseamar_files(vehicle, mission, file_type):
	"""
	Name:       get_alseamar_files
	Created:    2023-03-06

	Modified:   2023-03-06
	Author:     bob.currier@gcoos.org
	Notes:      Get list of files in data dir.  Update: added status test
				for deployed/recovered
	"""
	config = get_vehicle_config(vehicle)
	data_dir_root = config['gandalf']['post_data_dir_root']
	data_dir = '%s/%s' % (data_dir_root, 'data_files')

	alseamar_file_glob = '%s/*%s*' % (data_dir,file_type)

	logging.info('get_alseamar_files(%s): Using glob %s' %(vehicle,
				 alseamar_file_glob))
	alseamar_files = natsorted(glob.glob(alseamar_file_glob))
	logging.info('get_alseamar_files(%s) found %d files' %
	(vehicle, len(alseamar_files)))
	if len(alseamar_files) == 0:
		logging.warning("get_alseamar_files(%s): No files found. Skipping...",
						vehicle)
		return False
	return(alseamar_files)


def alseamar_to_df(vehicle, the_files):
	"""
	Author: 	robertdcurrier@gmail.com
	Created: 	2023-03-07
	Modified: 	2023-03-07
	Notes: 		
	"""
	delim = ';' # < --- MUST BE IN CONFIG FILE, YO
	frames = []
	logging.info('alseamar_to_df(%s)', vehicle)
	# Do the gli dance
	for file_name in the_files:
		data_frame = pd.read_csv(file_name,sep=delim)
		frames.append(data_frame)
	
	df = pd.concat(frames)
	return(df)


def df_to_mongo(vehicle, df, db):
	"""
	Author: 	robertdcurrier@gmail.com
	Created: 	2023-03-08
	Modified: 	2023-03-08
	Notes: 		InsertsMany df into MongoDB collection
	"""
	logging.info('df_to_mongo(%s)', vehicle)
	alseamar_json = json.loads(df.to_json(orient='records'))
	try:
	    db[vehicle].insert_many(alseamar_json)
	except:
	    logging.warning('df_to_mongo(%s): MongoDB insert failed', vehicle)


def chunk_it(vehicle):
    """
    Take one large collection, divide it into num_chunk chunks
    and iterate over collection returning len(df)/num_chunk documents.
    Convert each list into data frames and append to chunks[]. 
    When complete, pd.concat(chunks) and return single df.

    2023-03-09: We really just return one big chunk. We used this for
    sg_DIM, but don't need it for plots. We kept the name just in case 
    we need to restore chunking. This would better off being named as
    get_mongo() or something like that...
    """
    chunk_start = 0
    chunk_size = 500000
    chunk_end = chunk_size

    chunks = []
    logging.info('chunk_it(%s)', vehicle)

    try:
        client = connect_mongo()
    except:
        logging.warning('chunk_it(): Failed to connect to MongoDB')
        sys.exit()

    db = client.gandalf
    numdocs = db[vehicle].count_documents({})
    
    logging.info('chunk_it(%s): Found %d documents', vehicle, numdocs)
    results = (db[vehicle].find({}))
    df = pd.DataFrame(results)
   
    return df


def gandalf_alseamar_plots(vehicle, db):
    """
    Here's where it all begins....
    2023-02-08: Converting from CSV to MongoDB. Now we connect to Mongo,
    do a db[vehicle].find() and convert to a DF which we pass to the plotting
    routine.
    2023-02-14: Added chunk_it() from sg_track to chunk large DB
    and reduce memory usage
    """
    logging.info('gandalf_alseamar_plots(%s)' % vehicle)
    config = get_vehicle_config(vehicle)
    plot_sensor_list = config['gandalf']['plots']['plot_sensor_list']
    register_cmocean()
    # We need to get Depth Avg Currents working but will leave out while we
    # are transitioning to MongoDB.
    try:
        client = connect_mongo()
    except:
        logging.warning('gandalf_alseamar_plots(%s): MongoDB connect fail',
        				vehicle)
        sys.exit()

    db = client.gandalf
    logging.info('gandalf_alseamar_plots(%s): Creating DF from MongoDB collection',
     			 vehicle)
    
    df = chunk_it(vehicle)
    sort_field = 'epoch'
    df = df.sort_values(by = [sort_field], ascending=[True])
   
   
    df_len = (len(df))
    if df_len == 0:
        logging.debug('plot_sensor(): Empty Data Frame')
        return

    # THIS BE FOR TOMORROW TO DO
    for sensor in plot_sensor_list:
    	plot_sensor(config, vehicle, sensor, df)



def plot_sensor(config, vehicle, sensor, df):
    """
    Really need to refactor and clean. Far too long for single function.
    """
    
    logging.info('plot_sensor(%s): %s' % (vehicle, sensor))
    fig = config_date_axis(config, vehicle)
    status = flight_status(vehicle)

    print(df['LEGATO_TEMPERATURE'].min(),
     df['LEGATO_TEMPERATURE'].max())
    print(df['LEGATO_SALINITY'].min(),
     df['LEGATO_SALINITY'].max())

    # Get config settings
    sensors = get_sensor_config(vehicle)

    alt_colormap = config['gandalf']['plots']['alt_colormap']
    if alt_colormap:
        for index, value in enumerate(sensors):
            if value["sensor"] == sensor:
                cmap = value["alt_colormap"]
    else:
        cmap = 'jet'

    logging.info("plot_sensor(): using %s colormap for %s" % (cmap, sensor))

    for index, value in enumerate(sensors):
            if value["sensor"] == sensor:
                log_scale = bool(value["log_scale"])
                logging.debug("plot_sensor(%s): Log scale is %s" %
                              (sensor, log_scale))

    # Start and End date/time
    start_date = (time.strftime("%Y-%m-%d",
                  time.strptime(config["trajectory_datetime"],
                                "%Y%m%dT%H%M%S")))

    end_date = df['Timestamp'].iloc[-1]

    end_date = time.strptime(end_date, "%m/%d/%Y %H:%M:%S")
    end_date = time.strftime("%Y-%m-%d", end_date)

    logging.info("plot_sensor(): plotting %s" % sensor)
    logging.info("plot_sensor(): start_date %s" % start_date)
    logging.info("plot_sensor(): end_date %s" % end_date)

    # Title and subtitle
    for record in sensors:
        if (record['sensor'] == sensor):
            subtitle_string = "%s %s" % (record['sensor_name'],
                                         record['unit_string'])
            break
    title_string = "%s %s to %s\n %s" % (config['gandalf']['public_name'],
                                         start_date, end_date, subtitle_string)
    plt.title(title_string, fontsize=12, horizontalalignment='center')
   
    # Set plot ranges to account for over/under spikes
    (sensor_min, sensor_max) = normalize_sensor_range(sensor, vehicle, df)

    plt.gca().invert_yaxis()

    # SCATTER IT
    # check for alt_colormaps
    if config['gandalf']['plots']['alt_colormap']:
        logging.debug('Using alt_colormap...')
    

    #max_depth = max(df['Depth'])
    #plt.ylim(max_depth + config['gandalf']['plots']['plot_depth_padding'])

    plt.scatter(mpd.epoch2num(df['epoch']),
                df[sensor], s=15,
                c=df[sensor],
                lw=0, marker='8', cmap=cmap)
   
    if status == 'deployed':
        plot_dir = config['gandalf']['plots']['deployed_plot_dir']
    else:
        plot_dir = config['gandalf']['plots']['postprocess_plot_dir']
    plt.colorbar().set_label(config.get(
                             sensor, record['unit_string']), fontsize=10)
    plt.clim(sensor_min, sensor_max)

    # add_logo(vehicle, fig)

    if status == 'deployed':
        plot_dir = config['gandalf']['plots']['deployed_plot_dir']
    else:
        plot_dir = config['gandalf']['plots']['postprocess_plot_dir']

    # UPDATE CHECK for sensor_file command line arg and if true write local
    if len(sys.argv) == 4:
            plot_file = "/data/gandalf/tmp/%s.png" % (sensor)
    else:
        # Use config file settings
        plot_file = "%s/%s.png" % (plot_dir, sensor)
    logging.info("plot_sensor(): Writing %s" % (plot_file))
    plt.savefig(plot_file, dpi=100)
    # close figure
    plt.close(fig)
    logging.debug("plot_sensor(): Collecting garbage...")
    gc.collect()



def alseamar_process(vehicle, mission):
	"""
	
	Author: 	robertdcurrier@gmail.com
	Created: 	2023-02-21
	Modified: 	2023-03-06
	Notes: 		Main entry point
	"""
	config = get_vehicle_config(vehicle)
	client = connect_mongo()
	db = client.gandalf
	logging.info('alseamar_process(%s): Purging DB', vehicle)
	db[vehicle].drop()

	the_files = []
	logging.info('alseamar_process(%s)', vehicle)
	# Grab the gli files
	gli_files = get_alseamar_files(vehicle, mission, 'gli')
	the_files.append(gli_files)

	# Ditto for the pld1 files
	pld1_files = get_alseamar_files(vehicle, mission, 'pld1')
	the_files.append(pld1_files)

	gli_df = alseamar_to_df(vehicle, gli_files)

	sort_field = 'Timestamp' # <----- CONFIG FILE BITCH!
	mission_start = '01/08/2022 02:29:51' # <----- CONFIG FILE BITCH!
	gli_df = gli_df[gli_df[sort_field] > mission_start]
	# Create an epoch column for matplotlib
	
	# OKAY HERE WE HAVE TROUBLE WITH EUROPEAN DATE FORMAT -- FUCK IT,
	# WE WILL JUST CONVERT MANUALLY FOR THE TESTING WITH VOTO

	gli_df['epoch'] = (pd.to_datetime(gli_df['Timestamp']).
		values.astype(np.int64) // 10 ** 9) # <--- HELLAH YEAH THIS IS IT

	pld1_df = alseamar_to_df(vehicle, pld1_files)
	pld1_df['epoch'] = (pd.to_datetime(pld1_df['PLD_REALTIMECLOCK']).
		values.astype(np.int64) // 10 ** 9) # <--- DITTO
	
	df_to_mongo(vehicle, gli_df, db)
	df_to_mongo(vehicle, pld1_df, db)

	gandalf_alseamar_plots(vehicle, db)


if __name__ == '__main__':
	logging.basicConfig(level=logging.INFO)
	start_time = time.time()
	alseamar_process('sea063', 'm40')
	end_time = time.time()
	minutes = ((end_time - start_time) / 60)
	logging.info('Duration: %0.2f minutes' % minutes)
