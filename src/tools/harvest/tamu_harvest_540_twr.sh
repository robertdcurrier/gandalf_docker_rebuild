#!/bin/bash

# Get unit_540 from sfmc.webbresearch.com
# sbd files
cd /data/gandalf/deployments/tamu/unit_540/binary_files/sbd
echo "Getting unit_540 sbd files from sfmc.webbresearch.com"
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/tamu/gliders/unit_540/from-glider/unit_*.sbd .
# tbd files
echo "Getting unit_540 tbd files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/tamu/unit_540/binary_files/tbd
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/tamu/gliders/unit_540/from-glider/unit_*.tbd .

# log files
echo "Getting unit_540 log files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/tamu/unit_540/ascii_files/logs
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/tamu/gliders/unit_540/logs/*.log .
