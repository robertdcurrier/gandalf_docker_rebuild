#!/bin/bash
echo "Harvesting angus..."
DATA_DIR="/data/gandalf/deployments/skio/angus"
echo $DATA_DIR
echo "Rsyncing log files from skiogliderserver for angus"
rsync -av gcoos@sfmc.skio.uga.edu:/var/opt/sfmc-dockserver/stations/default/gliders/angus/logs/angus*.log "$DATA_DIR/ascii_files/logs/"
echo "Rsyncing sbd files from skiogliderserver for angus"
rsync -av gcoos@sfmc.skio.uga.edu:/var/opt/sfmc-dockserver/stations/default/gliders/angus/from-glider/angus-2024*.sbd "$DATA_DIR/binary_files/sbd/"
echo "Rsyncing tbd files from skiogliderserver for angus"
rsync -av gcoos@sfmc.skio.uga.edu:/var/opt/sfmc-dockserver/stations/default/gliders/angus/from-glider/angus-2024*.tbd "$DATA_DIR/binary_files/tbd/"
echo "Completed run at: " `date`

