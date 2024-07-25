#!/usr/bin/env python3
"""
Created:    2023-08-24
Modified:   2023-09-12
Author:     bob.currier@gcoos.org
Notes:      Harvests RTOF .nc4 file for GANDALF ncWMS2
"""
import sys
import logging
from urllib.request import urlopen
from datetime import date
from datetime import timedelta

def fetch_rtofs():
    """
    Author:     robertdcurrier@gmail.com
    Created:    2023-08-24
    Modified:   2023-09-12
    Notes:      Uses bbox-subsetted URL to retrieve daily RTOFS run
                Added automatic date append to url string
    """
    today = date.today()
    yesterday = today - timedelta(days=1)
    timestamp = "%sT00" % yesterday
    
    url = "https://ncss.hycom.org/thredds/ncss/GLBy0.08/expt_93.0/\
FMRC/GLBy0.08_930_FMRC_best.ncd?var=salinity_bottom&var=surf_el&var=\
water_temp_bottom&var=water_u_bottom&var=water_v_bottom&var=salinity&var=\
water_temp&var=water_u&var=water_v&north=45.00&west=-100&east=-65&south=\
10.0000&disableProjSubset=on&horizStride=1&time=" + timestamp
    url = url + "%3A00%3A00Z&vertCoord=&accept=netcdf4"
   
    logging.info('fetch_rtofs(): Inititiating download...')
    with urlopen(url) as file:
        try:
            content = file.read()
        except:
            logging.warning('fetch_rtofs(): Failed to download content.')
            sys.exit()

    try:
        out_file = open("/data/gandalf/ncwms/GLBy0.08_930_FMRC_best.nc4", "wb")
        out_file.write(content)
    except:
        logging.warning('fetch_rtofs(): Failed to write content to file.')
        sys.exit()

    logging.info('fetch_rtofs(): Downloaded and saved GLBy0 successfully.')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetch_rtofs()




