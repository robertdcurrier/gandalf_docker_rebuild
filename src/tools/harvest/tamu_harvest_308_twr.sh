#!/bin/bash

# Get unit_308 from sfmc.webbresearch.com
# sbd files
cd /data/gandalf/deployments/tamu/unit_308/binary_files/sbd
echo "Getting unit_308 sbd files from sfmc.webbresearch.com"
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/tamu/gliders/unit_308/from-glider/unit_*.sbd .
# tbd files
echo "Getting unit_308 tbd files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/tamu/unit_308/binary_files/tbd
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/tamu/gliders/unit_308/from-glider/unit_*.tbd .

# log files
echo "Getting unit_308 log files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/tamu/unit_308/ascii_files/logs
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/tamu/gliders/unit_308/logs/*.log .
