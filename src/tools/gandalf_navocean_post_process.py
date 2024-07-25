#!/usr/bin/python3
import sys
from gandalf_slocum_binaries_v2 import flight_status
"""
post-process.py: Simple script to post-process vehicle data.
gandalf_mcp runs on a timed loop, and rather than complicate
that code it was easier to write a tool specifically for
post-processing.
"""

def write_post_geojson(vehicle, data):
    """
    DOCSTRING
    """
    print("write_post_geojson(%s)" % vehicle)
    config = get_vehicle_config(vehicle)
    dpath = (config['gandalf']['post_data_dir_root'])
    fname = ("%s/processed_data/%s.json" % (dpath, vehicle))
    print("write_post_geojson(): Writing %s" % fname)
    outf = open(fname,'w')
    print(data, file=outf)
    outf.flush()
    outf.close()

def init_app():
    """
    Call everything from here so we avoid pylint
    grumbling about constants in __main__
    """
    if len(sys.argv) != 2:
        print("Usage: gandalf_navocean_post_process vehicle")
        sys.exit()
    else:
        vehicle = sys.argv[1]
    status = flight_status(vehicle)
    if status != 'recovered':
        print("gandalf_post_process(): %s must be recovered to post-process!"
              %  vehicle)
        sys.exit()
    else:
        print("%s is recovered. Proceeding..." % vehicle)

if __name__ == '__main__':
    init_app()

