#!/usr/bin/env python3
"""
Name:       gandalf_calc_sensors.py
Created:    2016-09-07
Modified:   2020-10-15
Author:     bob.currier@gcoos.org
Notes:      Uses seawater to calculate salinity and sigma-t. Modifies DataFrame
            and adds calc_sensors to end of row.
            Changed from print() to logging.warn/debug
"""
import sys
import json
import logging
import pandas as pd
import seawater as sw
from gandalf_utils import get_vehicle_config, flight_status


def calc_salinity(config, vehicle):
    """
    Read sensors.csv as data_frame. Create cond, temp, press series.
    Add calc_salinity and calc_density columns to df.
    Spin through df and write calculated values.
    Write updated sensors.csv to file.
    """
    logging.info('calc_salinity(%s)' % vehicle)
    status = flight_status(vehicle)
    # Deployed
    if status == 'deployed':
        root_dir = config['gandalf']['deployed_data_dir']
    # Post-Process
    if status == 'recovered':
        root_dir = config['gandalf']['post_data_dir_root']

    #read CSV
    file_name = "%s/processed_data/sensors.csv" % (root_dir)
    logging.debug("calc_salinity(): status %s" % status)
    logging.debug("calc_salinity(): root_dir %s" % root_dir)
    logging.debug("calc_salinity(): file_name = %s"% file_name)

    data_frame = pd.read_csv(file_name)
    df_len = (len(data_frame))
    if df_len == 0:
        logging.debug('calc_salinity(): Empty Data Frame')
        return

    #add column for calc_sal_df
    data_frame['calc_salinity'] = 0
    #add columns for sci_water_cond and sci_water_pressure
    #Now we map the seawater salinity formula over the DF
    for _ in data_frame:
        data_frame.calc_salinity = (sw.salt(data_frame['sci_water_cond']*
                                            0.23302418791070513,
                                            data_frame['sci_water_temp'],
                                            data_frame['sci_water_pressure']))
    #pylint: disable=maybe-no-member
    data_frame.to_csv(file_name, na_rep='NaN', index=False)


def calc_density(config, vehicle):
    """
    Read sensors.csv as data_frame. Create cond, temp, press series.
    Add calc_salinity and calc_density columns to df.
    Spin through df and write calculated values.
    Write updated sensors.csv to file.
    """
    logging.info('calc_density(%s)' % vehicle)
    status = flight_status(vehicle)
    # Deployed
    if status == 'deployed':
        root_dir = config['gandalf']['deployed_data_dir']
    # Post-Process
    if status == 'recovered':
        root_dir = config['gandalf']['post_data_dir_root']

    #read CSV
    file_name = "%s/processed_data/sensors.csv" % (root_dir)

    logging.debug("calc_density(): status %s" % status)
    logging.debug("calc_density(): root_dir %s" % root_dir)
    logging.debug("calc_density(): file_name = %s" % file_name)

    data_frame = pd.read_csv(file_name)
    df_len = (len(data_frame))
    if df_len == 0:
        logging.debug('calc_density(): Empty Data Frame')
        logging.debug('calc_sigma(): Empty Data Frame')
        return

    # add columns for calc_density and calc_sigma
    data_frame['calc_density'] = 0
    data_frame['calc_sigma'] = 0
    # Now we map the seawater densityformula over the DF
    for _ in data_frame:
        data_frame['calc_sigma'] = (sw.dens(data_frame['calc_salinity'],
                                            data_frame['sci_water_temp'],
                                            data_frame['sci_water_pressure'])
                                    - 1000)
    for _ in data_frame:
        data_frame['calc_density'] = (sw.dens(data_frame['calc_salinity'],
                                              data_frame['sci_water_temp'],
                                              data_frame['sci_water_pressure'])
                                      )
    data_frame.to_csv(file_name, na_rep='NaN', index=False)


def calc_soundvel(config, vehicle):
    """
    2019-09-24 robertdcurrier@gmail.com
    Reinstated calc sound as we now have
    Navy gliders in the GOM, and a USM
    Seaglider. Getting down to 1,000 meters
    which makes it worth calculating sound vel
    so we can hunt the Russian wumpus.
    """
    logging.info('calc_soundvel(%s)' % vehicle)
    status = flight_status(vehicle)
    # Deployed
    if status == 'deployed':
        root_dir = config['gandalf']['deployed_data_dir']
    # Post-Process
    if status == 'recovered':
        root_dir = config['gandalf']['post_data_dir_root']

    #read CSV
    file_name = "%s/processed_data/sensors.csv" % (root_dir)

    logging.debug("calc_soundvel(): status %s" % status)
    logging.debug("calc_soundvel(): root_dir %s" % root_dir)
    logging.debug("calc_soundvel(): file_name = %s"% file_name)

    data_frame = pd.read_csv(file_name)
    df_len = (len(data_frame))
    if df_len == 0:
        logging.debug('calc_soundvel(): Empty Data Frame')
        return

    #add column for calc_density
    data_frame['calc_soundvel'] = 0
    #Now we map the seawater densityformula over the DF
    for _ in data_frame:
        data_frame['calc_soundvel'] = sw.svel(data_frame['sci_water_temp'],
                                              data_frame['calc_salinity'],
                                              data_frame['sci_water_pressure'])
    #pylint: disable=maybe-no-member
    data_frame.to_csv(file_name, na_rep='NaN', index=False)


if __name__ == '__main__':
    """
    For debug and testing
    """
    if len(sys.argv) !=2:
        logging.warn('usage: gandalf_calc_sensors vehicle')
        sys.exit()
    vehicle = sys.argv[1]
    config = get_vehicle_config(vehicle)
    calc_salinity(config, vehicle)
    calc_density(config, vehicle)
    calc_soundvel(config, vehicle)
