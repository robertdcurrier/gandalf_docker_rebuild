#!/bin/bash

# Get mote-genie from sfmc.webbresearch.com
# sbd files
cd /data/gandalf/deployments/mote/mote-genie/binary_files/sbd
echo "Getting mote-genie sbd files from sfmc.webbresearch.com"
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/mote/gliders/mote-genie/from-glider/mote-genie-2022*.sbd .
# tbd files
echo "Getting mote-genie tbd files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/mote/mote-genie/binary_files/tbd
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/mote/gliders/mote-genie/from-glider/mote-genie-2022*.tbd .

# log files
echo "Getting mote-genie log files from sfmc.webbresearch.com"
cd /data/gandalf/deployments/mote/mote-genie/ascii_files/logs
rsync -av rcurrier@sfmc.webbresearch.com:/var/opt/sfmc-dockserver/stations/mote/gliders/mote-genie/logs/*.log .


