#!/bin/bash

# Get unit_595 from sfmc.webbresearch.com
# sbd files
cd /data/gandalf/deployments/alaska/unit_595/binary_files/sbd
echo "Getting unit_595 sbd files from sfmc.webbresearch.com"
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/alaska/gliders/unit_595/from-glider/unit_595-2022*.sbd .
# tbd files
echo "Getting unit_595 tbd files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/alaska/unit_595/binary_files/tbd
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/alaska/gliders/unit_595/from-glider/unit_595-2022*.tbd .

# log files
echo "Getting unit_595 log files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/alaska/unit_595/ascii_files/logs
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/alaska/gliders/unit_595/logs/*.log .
echo 'Done!'
