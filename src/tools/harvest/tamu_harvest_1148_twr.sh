#!/bin/bash

# Get unit_1148 from sfmc.webbresearch.com
# sbd files
cd /data/gandalf/deployments/tamu/unit_1148/binary_files/sbd
echo "Getting unit_1148 sbd files from sfmc.webbresearch.com"
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/tamu/gliders/unit_1148/from-glider/unit_1148-2024*.sbd .
# tbd files
echo "Getting unit_1148 tbd files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/tamu/unit_1148/binary_files/tbd
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/tamu/gliders/unit_1148/from-glider/unit_1148-2024*.tbd .

# log files
echo "Getting unit_1148 log files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/tamu/unit_1148/ascii_files/logs
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/tamu/gliders/unit_1148/logs/unit_1148_2024*.log .
