#!/bin/bash
echo "Harvesting salacia..."
DATA_DIR="/data/gandalf/deployments/skio/salacia"
echo $DATA_DIR
echo "Rsyncing log files from skiogliderserver for salacia"
rsync -av secoora@sfmc.skio.uga.edu:/var/opt/sfmc-dockserver/stations/default/gliders/salacia/logs/salacia_202109*.log "$DATA_DIR/ascii_files/logs/"
echo "Rsyncing sbd files from skiogliderserver for salacia"
rsync -av secoora@sfmc.skio.uga.edu:/var/opt/sfmc-dockserver/stations/default/gliders/salacia/from-glider/salacia-2021*.sbd "$DATA_DIR/binary_files/sbd/"
echo "Rsyncing tbd files from skiogliderserver for salacia"
rsync -av secoora@sfmc.skio.uga.edu:/var/opt/sfmc-dockserver/stations/default/gliders/salacia/from-glider/salacia-2021*.tbd "$DATA_DIR/binary_files/tbd/"
echo "Completed run at: " `date`

