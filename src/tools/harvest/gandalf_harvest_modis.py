#!/usr/bin/python3
"""
Name: gandalf_harvest_modis
Author: robertdcurrier@gmail.com
Date: 2020-05-08
Modified: 2023-09-01

Notes: Fetches latest processed MODIS folder from USF
and deposits 7D CHL and SST in /data/gandalf/modis

We had to write this app as USF changed the naming
convention for their folders/files and made them into
non-predictable terms.  They are not generated on a regular
schedule making the old covention of DOY break.

SSL is breaking. We need to migrate this to urlib.request
as we used for rtofs and ssh. Until then, we be broked.
"""
import requests
from urllib.request import urlopen
import sys
import ssl
import os
from datetime import datetime

#Globals -- why use configparser for such a short app
BASE_URL = "http://optics.marine.usf.edu/subscription/modis/GCOOS/2024/comp"
DATA_DIR = "/data/gandalf/modis/"
DEBUG = True

def fetch_files():
    """
    Grab 7Day CHL and SST files from fetch_url.
    Put them in DATA_DIR and rename to sst.png and chl.png
    """
    context = ssl._create_unverified_context()
    # - 2 as they are out of sync
    modis_day = datetime.now().timetuple().tm_yday - 2
    md_6 = modis_day - 6
    fetch_url = BASE_URL + "/%03d/" % modis_day

    #CHL
    file_url = ""
    fname = ("A2024" + "%03d" + "2024" + "%03d" +
    ".1KM.GCOOS.7DAY.L3D.CHL.png") % (md_6, modis_day)

    file_url = fetch_url + fname


    with urlopen(file_url, context=context) as file:
        try:
            chl = file.read()
        except:
            sys.exit()

    with open(DATA_DIR + 'chl.png', 'wb') as f:
        f.write(chl)
    print('fetch_files(): Wrote chl.png')

    #SST
    file_url = ""
    fname = ("C2024" + "%03d" + "2024" + "%03d" +
    ".1KM.GCOOS.7DAY.L3D.SST.png") % (md_6, modis_day)

    file_url = fetch_url + fname
    if DEBUG:
        print("Fetching sst from %s" % file_url)
    sst = requests.get(file_url)
    with open(DATA_DIR + 'sst.png', 'wb') as f:
        f.write(sst.content)


def init_app():
    """
    Kick it
    """
    fetch_files()


if __name__ == '__main__':
    init_app()
