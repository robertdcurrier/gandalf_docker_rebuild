#!/bin/bash
echo "Harvesting pelagia..."
DATA_DIR="/data/gandalf/deployments/skio/pelagia"
echo $DATA_DIR
echo "Rsyncing log files from skiogliderserver for pelagia"
rsync -av secoora@sfmc.skio.uga.edu:/var/opt/sfmc-dockserver/stations/default/gliders/pelagia/logs/pelagia_202109*.log "$DATA_DIR/ascii_files/logs/"
echo "Rsyncing sbd files from skiogliderserver for pelagia"
rsync -av secoora@sfmc.skio.uga.edu:/var/opt/sfmc-dockserver/stations/default/gliders/pelagia/from-glider/pelagia-2021*.sbd "$DATA_DIR/binary_files/sbd/"
echo "Rsyncing tbd files from skiogliderserver for pelagia"
rsync -av secoora@sfmc.skio.uga.edu:/var/opt/sfmc-dockserver/stations/default/gliders/pelagia/from-glider/pelagia-2021*.tbd "$DATA_DIR/binary_files/tbd/"
echo "Completed run at: " `date`

