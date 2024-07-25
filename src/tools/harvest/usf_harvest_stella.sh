#!/bin/bash
echo "Harvesting usf-stella..."
DATA_DIR="/data/gandalf/deployments/usf/usf-stella"
echo $DATA_DIR
echo "Rsyncing log files from usfgliderserver for usf-stella"
rsync -av gcoos@usfgliderserver.marine.usf.edu:/var/opt/sfmc-dockserver/stations/default/gliders/usf-stella/logs/*.log "$DATA_DIR/ascii_files/logs/"
echo "Rsyncing sbd files from usfgliderserver for usf-stella"
rsync -av gcoos@usfgliderserver.marine.usf.edu:/var/opt/sfmc-dockserver/stations/default/gliders/usf-stella/from-glider/usf-stella*.sbd "$DATA_DIR/binary_files/sbd/"
echo "Rsyncing tbd files from usfgliderserver for usf-stella"
rsync -av gcoos@usfgliderserver.marine.usf.edu:/var/opt/sfmc-dockserver/stations/default/gliders/usf-stella/from-glider/usf-stella*.tbd "$DATA_DIR/binary_files/tbd/"
echo "Completed run at: " `date`

