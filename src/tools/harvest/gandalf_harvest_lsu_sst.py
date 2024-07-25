#!/usr/bin/env python3
"""
We fetch the latest SST, dilly dilly!
"""
import sys
import ssl
import logging
from urllib.request import urlopen

def fetch_sst():
    """
    Author:     robertdcurrier@gmail.com
    Created:    2023-08-25
    Modified:   2023-08-25
    Notes:      Fetches daily LSU SST run
    """
    context = ssl._create_unverified_context()
    url = "https://www.esl.lsu.edu/GCOOS/latest_SST.nc"
    logging.info('fetch_sst(): Initiating download...')
    with urlopen(url, context=context) as file:
        try:
            content = file.read()
        except:
            logging.warning('fetch_sst(): Failed to download content.')
            sys.exit()

    try:
        out_file = open("/data/gandalf/ncwms/latest_SST.nc", "wb")
        out_file.write(content)
    except:
        logging.warning('fetch_sst(): Failed to write content to file.')
        sys.exit()

    logging.info('fetch_sst(): Downloaded and saved latest_SST successfully.')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetch_sst()




