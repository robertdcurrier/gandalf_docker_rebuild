#!/bin/bash

# Get unit_1139 from sfmc.webbresearch.com
# sbd files
cd /data/gandalf/deployments/mote/mote-SeaXplorer/binary_files/sbd
echo "Getting unit_1139 sbd files from sfmc.webbresearch.com"
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/mote/gliders/unit_1139/from-glider/unit_1139-2024*.sbd .
# tbd files
echo "Getting unit_1139 tbd files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/mote/mote-SeaXplorer/binary_files/tbd
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/mote/gliders/unit_1139/from-glider/unit_1139-2024*.tbd .

# log files
echo "Getting unit_1139 log files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/mote/mote-SeaXplorer/ascii_files/logs
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/mote/gliders/unit_1139/logs/*.log .
echo 'Done!'

