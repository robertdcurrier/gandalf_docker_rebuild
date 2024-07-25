#!/bin/bash
echo "Harvesting franklin..."
DATA_DIR="/data/gandalf/deployments/skio/franklin"
echo $DATA_DIR
echo "Rsyncing log files from skiogliderserver for franklin"
rsync -av gcoos@sfmc.skio.uga.edu:/var/opt/sfmc-dockserver/stations/default/gliders/franklin/logs/franklin*.log "$DATA_DIR/ascii_files/logs/"
echo "Rsyncing sbd files from skiogliderserver for franklin"
rsync -av gcoos@sfmc.skio.uga.edu:/var/opt/sfmc-dockserver/stations/default/gliders/franklin/from-glider/franklin-2023*.sbd "$DATA_DIR/binary_files/sbd/"
echo "Rsyncing tbd files from skiogliderserver for franklin"
rsync -av gcoos@sfmc.skio.uga.edu:/var/opt/sfmc-dockserver/stations/default/gliders/franklin/from-glider/franklin-2023*.tbd "$DATA_DIR/binary_files/tbd/"
echo "Completed run at: " `date`

