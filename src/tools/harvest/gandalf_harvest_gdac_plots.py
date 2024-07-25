#!/usr/bin/python3
"""
Name: gandalf_harvest_gdac_plots
Author: bob.currier@gcoos.org
Date: 2018-08-24
Notes:
Retrieves temp, density and salinity from GDAC
and stores in /data/gandalf/gandalf_config/vehicle/plots
We will eventually be rolling our own using Pandas and the
full CSV file but for now this is the quick and easy way
to get plots working.
"""
import sys
import requests
import json
DEBUG = True

def get_gdac_plots(vehicle):
    """
    Fetch plots from GDAC
    """
    if DEBUG:
        print("get_gdac_plots(%s)" % vehicle)
    # get config info for each vehicle
    vehicle_config = ("/data/gandalf/gandalf_configs/%s/ngdac/deployment.json"
                      % vehicle)
    config = open(vehicle_config,'r').read();
    config = json.loads(config)
    plots_url = config["gandalf"]["gdac_plots_url"]
    print(plots_url)
    png = requests.get(plots_url)


def init_app():
    """
    Kick it
    """
    get_gdac_plots('ng645')


if __name__ == '__main__':
    init_app()
