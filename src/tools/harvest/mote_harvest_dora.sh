#!/bin/bash

# Get unit_839 from sfmc.webbresearch.com
# sbd files
cd /data/gandalf/deployments/mote/mote-dora/binary_files/sbd
echo "Getting unit_839 sbd files from sfmc.webbresearch.com"
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/mote/gliders/unit_839/from-glider/unit_839-2024*.sbd .
# tbd files
echo "Getting unit_839 tbd files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/mote/mote-dora/binary_files/tbd
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/mote/gliders/unit_839/from-glider/unit_839-2024*.tbd .

# log files
echo "Getting unit_839 log files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/mote/mote-dora/ascii_files/logs
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/mote/gliders/unit_839/logs/*.log .
echo 'Done!'

