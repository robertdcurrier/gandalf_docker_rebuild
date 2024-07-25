#!/usr/bin/env python3
import json
import sys

data_path = '/data/gandalf/deployments/geojson'
v_type = 'local'
vehicle_types = ['local', 'seagliders']
# Loop over all vehicle types (local, erddap, navocean)
for v_type in vehicle_types:
    # For each type grab config file and convert to json
    config_file = '%s/%s.json' % (data_path, v_type)
    the_config = (open(config_file).read())
    if len(the_config) != 0:
        the_config = json.loads(the_config)
        # Go through each vehicle type config file and pull out vehicles
        for vehicle in the_config:
            for feature in vehicle['features']:
                print(feature)
