#!/bin/bash
echo "Harvesting unit_1091..."
DATA_DIR="/data/gandalf/deployments/skio/unit_1091"
echo $DATA_DIR
echo "Rsyncing log files from skiogliderserver for unit_1091"
rsync -av gcoos@sfmc.skio.uga.edu:/var/opt/sfmc-dockserver/stations/default/gliders/unit_1091/logs/unit_1091*.log "$DATA_DIR/ascii_files/logs/"
echo "Rsyncing sbd files from skiogliderserver for unit_1091"
rsync -av gcoos@sfmc.skio.uga.edu:/var/opt/sfmc-dockserver/stations/default/gliders/unit_1091/from-glider/unit_1091-2023*.sbd "$DATA_DIR/binary_files/sbd/"
echo "Rsyncing tbd files from skiogliderserver for unit_1091"
rsync -av gcoos@sfmc.skio.uga.edu:/var/opt/sfmc-dockserver/stations/default/gliders/unit_1091/from-glider/unit_1091-2023*.tbd "$DATA_DIR/binary_files/tbd/"
echo "Completed run at: " `date`

