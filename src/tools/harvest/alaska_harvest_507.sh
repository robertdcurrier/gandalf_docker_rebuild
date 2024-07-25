#!/bin/bash

# Get unit_507 from sfmc.webbresearch.com
# sbd files
cd /data/gandalf/deployments/alaska/unit_507/binary_files/sbd
echo "Getting unit_507 sbd files from sfmc.webbresearch.com"
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/alaska/gliders/unit_507/from-glider/unit_507-2023*.sbd .
# tbd files
echo "Getting unit_507 tbd files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/alaska/unit_507/binary_files/tbd
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/alaska/gliders/unit_507/from-glider/unit_507-2023*.tbd .

# log files
echo "Getting unit_507 log files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/alaska/unit_507/ascii_files/logs
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/alaska/gliders/unit_507/logs/*.log .
echo 'Done!'
