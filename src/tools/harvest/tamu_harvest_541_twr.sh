#!/bin/bash

# Get unit_541 from sfmc.webbresearch.com
# sbd files
cd /data/gandalf/deployments/tamu/unit_541/binary_files/sbd
echo "Getting unit_541 sbd files from sfmc.webbresearch.com"
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/tamu/gliders/unit_541/from-glider/unit_541-2023*.sbd .
# tbd files
echo "Getting unit_541 tbd files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/tamu/unit_541/binary_files/tbd
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/tamu/gliders/unit_541/from-glider/unit_541-2023*.tbd .

# log files
echo "Getting unit_541 log files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/tamu/unit_541/ascii_files/logs
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/tamu/gliders/unit_541/logs/unit_541_2023*.log .
