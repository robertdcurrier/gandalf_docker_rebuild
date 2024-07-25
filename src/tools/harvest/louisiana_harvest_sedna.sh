#!/bin/bash

# Get sedna from sfmc.webbresearch.com
# sbd files
cd /data/gandalf/deployments/louisiana/sedna/binary_files/sbd
echo "Getting sedna sbd files from sfmc.webbresearch.com"
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/louisiana/gliders/sedna/from-glider/sedna*.sbd .
# tbd files
echo "Getting sedna tbd files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/louisiana/sedna/binary_files/tbd
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/louisiana/gliders/sedna/from-glider/sedna*.tbd .

# log files
echo "Getting sedna log files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/louisiana/sedna/ascii_files/logs
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/louisiana/gliders/sedna/logs/*.log .
