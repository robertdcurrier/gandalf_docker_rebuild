#!/bin/bash

# Get unit_191 from sfmc.webbresearch.com
# sbd files
cd /data/gandalf/deployments/alaska/unit_191/binary_files/sbd
echo "Getting unit_191 sbd files from sfmc.webbresearch.com"
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/alaska/gliders/unit_191/from-glider/unit_191-2021*.sbd .
# tbd files
echo "Getting unit_191 tbd files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/alaska/unit_191/binary_files/tbd
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/alaska/gliders/unit_191/from-glider/unit_191-2021*.tbd .

# log files
echo "Getting unit_191 log files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/alaska/unit_191/ascii_files/logs
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/alaska/gliders/unit_191/logs/*.log .
echo 'Done!'
