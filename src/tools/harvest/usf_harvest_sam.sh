#!/bin/bash
echo "Harvesting usf-sam..."
DATA_DIR="/data/gandalf/deployments/usf/usf-sam"
echo $DATA_DIR
echo "Rsyncing log files from usfgliderserver for usf-sam"
rsync -av gcoos@usfgliderserver.marine.usf.edu:/var/opt/sfmc-dockserver/stations/default/gliders/usf-sam/logs/*.log "$DATA_DIR/ascii_files/logs/"
echo "Rsyncing sbd files from usfgliderserver for usf-sam"
rsync -av gcoos@usfgliderserver.marine.usf.edu:/var/opt/sfmc-dockserver/stations/default/gliders/usf-sam/from-glider/usf-sam-2024*.sbd "$DATA_DIR/binary_files/sbd/"
echo "Rsyncing tbd files from usfgliderserver for usf-sam"
rsync -av gcoos@usfgliderserver.marine.usf.edu:/var/opt/sfmc-dockserver/stations/default/gliders/usf-sam/from-glider/usf-sam-2024*.tbd "$DATA_DIR/binary_files/tbd/"
echo "Completed run at: " `date`

