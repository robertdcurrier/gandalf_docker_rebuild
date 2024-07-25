#!/usr/bin/env python3
"""
    Name:   gandalf_harvest_navocean
    Date:   2016-04-13
    Author: bob.currier@gcoos.org
    Notes:
    Retrieves JSON file containing currently deployed Navocean
    ASVs. Stores new updates in PostGIS table defined as JSON
"""
import wget
import re
import sys
import os
import json
from geojson import Feature, Point, FeatureCollection
DEBUG = True

def get_url():
    """
    DOCSTRING
    """
    vela_url = "http://portal.navocean.com/data/VELA_log.json"
    if DEBUG:
        print("get_url()...")
    out_dir = "/data/gandalf/deployments/geojson"
    response = wget.download(vela_url, out=out_dir)


def main():
    """
    DOCSTRING
    """
    the_json = get_url()

if __name__ == "__main__":
    if DEBUG:
        print("gandalf_harvest_navocean v1.0")
    main()
