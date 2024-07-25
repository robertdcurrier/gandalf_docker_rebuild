#!/usr/bin/env python3
"""
Created:    2023-09-14
Modified:   2023-09-14
Author:     bob.currier@gcoos.org
Notes:      Pulls png files of model comparison for deployed
            vehicles from Rutgers
"""
import logging
import sys
import os
import time
import regex
from natsort import natsorted
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import date
from datetime import timedelta
from urllib.request import urlopen
logging.basicConfig(level=logging.WARNING)
# GLOBALS --> Need to move to ngdac.json Gandalf section
model_root_url = "https://rucool.marine.rutgers.edu/hurricane/\
model_comparisons/profiles/gliders"
velocity_root_url = "https://rucool.marine.rutgers.edu/hurricane/\
GGS_Yucatan/data"
mod_output_dir = "/data/gandalf/deployments/model_comps"
velocity_output_dir = "/data/gandalf/ncwms/rutgers"
# END GLOBALS


def get_file_names(url, type):
    """
    Created:    2023-09-14
    Modified:   2024-02-18
    Author:     bob.currier@gcoos.org
    Notes:      Pulls png files of model comparison for deployed
                    vehicles from Rutgers
    """
    logging.info(f'get_file_names(): Using {url}')
    with urlopen(url) as file:
        try:
            raw_html = file.read()
        except:
            logging.warning(f'get_file_names(): Failed to load url')
            sys.exit()
    fnames = bs4_parse(raw_html, type)
    logging.debug(f'get_file_names(): Got {fnames}')
    return (fnames)


def bs4_parse(raw_html, type):
    """
    Created:    2023-09-14
    Modified:   2023-09-14
    Author:     bob.currier@gcoos.org
    Notes:      Uses BeautifulSoup to parse html doc from url
    """
    png_files = []
    logging.debug(f'bs4_parse()')
    soup = BeautifulSoup(raw_html, 'html.parser')
    # Select all a tags
    images = soup.select('a')
    # look only for png hrefs
    for fname in images:
        if type in str(fname):
            png_files.append(fname.text)
    return png_files


def fetch_files(fnames, comps_url, dest):
    """
    Created:    2023-09-14
    Modified:   2023-09-15
    Author:     bob.currier@gcoos.org
    Notes:      Retrieves deployed glider model png files from Rutgers
                2023-09-15 fixed bug in file_path
    """
    for the_file in fnames:
        file_path = f'{comps_url}/{the_file}'
        with urlopen(file_path) as file:
            logging.warning(f'modcomp_fetch_png_files(): Downloading {the_file}')
            try:
                content = file.read()
            except:
                logging.warning(f'fetch_rtofs(): Failed to download {the_file}')
                sys.exit()
        try:
            out_file = open(f'{dest}/{the_file}', "wb")
            out_file.write(content)
        except:
            logging.warning('modcomp_fetch_png_files(): Failed to write content to file.')
            sys.exit()


def rutgers_model_comps():
    """
    Created:    2023-09-14
    Modified:   2023-09-14
    Author:     bob.currier@gcoos.org
    Notes:      Main entry point
    """
    type = 'png'
    logging.info(f'gandalf_model_comps()')
    today = (date.today())
    # Yesterday to make sure all vehicles have updated
    yesterday = str(today - timedelta(days=1))
    (year,month,day) = yesterday.split('-')
    comps_url = f"{model_root_url}/{year}/{month}-{day}"

    fnames = get_file_names(comps_url, type)
    fetch_files(fnames, comps_url,mod_output_dir)


def rutgers_velocity_model():
    """
    Created:    2023-09-14
    Modified:   2024-02-18
    Author:     bob.currier@gcoos.org
    Notes:      Main entry point
    """
    type = "nc"
    logging.warning(f'rutgers_velocity_model()')
    today = str(date.today())
    today = today.replace('-','')
    # 2024-03-12 Rutgers code finally working again
    velocity_url = f"{velocity_root_url}/{today}"
    fnames = get_file_names(velocity_url, type)
    fnames = [natsorted(fnames)[-1]]
    fetch_files(fnames, velocity_url,velocity_output_dir)


def empty_folder(folder_path):
    """
    """
    logging.warning(f'empty_folder({folder_path})')
    # Loop through each item in the folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # Remove file or link
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Remove directory and all its contents
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    start_time = time.time()
    empty_folder(velocity_output_dir)
    empty_folder(mod_output_dir)
    try:
        rutgers_model_comps()
    except:
        logging.warning('Model Comps Failure')
    try:
        rutgers_velocity_model()
    except:
        logging.warning('Velocity Model Failure')
    end_time = time.time()

    minutes = round((end_time - start_time) / 60, 2)
    logging.warning(f'Duration: {minutes} minutes')

