#!/bin/bash
echo "Harvesting usf-gansett..."
DATA_DIR="/data/gandalf/deployments/usf/usf-gansett"
echo $DATA_DIR
echo "Rsyncing log files from usfgliderserver for usf-gansett"
rsync -av gcoos@usfgliderserver.marine.usf.edu:/var/opt/sfmc-dockserver/stations/default/gliders/usf-gansett/logs/*.log "$DATA_DIR/ascii_files/logs/"
echo "Rsyncing sbd files from usfgliderserver for usf-gansett"
rsync -av gcoos@usfgliderserver.marine.usf.edu:/var/opt/sfmc-dockserver/stations/default/gliders/usf-gansett/from-glider/*.sbd "$DATA_DIR/binary_files/sbd/"
echo "Rsyncing tbd files from usfgliderserver for usf-gansett"
rsync -av gcoos@usfgliderserver.marine.usf.edu:/var/opt/sfmc-dockserver/stations/default/gliders/usf-gansett/from-glider/*.tbd "$DATA_DIR/binary_files/tbd/"
echo "Completed run at: " `date`

