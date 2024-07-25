#SKIO Ramses
echo "Harvesting SKIO ramses"
#LOGS
cd /data/gandalf/deployments/skio/ramses/ascii_files/
echo "Getting ramses logs..."
wget  -q -r -l1 -nH --cut-dirs=3 http://dockserver.skio.uga.edu/gmc/gliders/ramses/logs/ -A "ramses_network_2018*.log"
#SBD
cd /data/gandalf/deployments/skio/ramses/binary_files/sbd
echo "Getting ramses sbd files..."
wget -q -r -l1 -nH --cut-dirs=4 http://dockserver.skio.uga.edu/gmc/gliders/ramses/from-glider/ -A "ramses-2018-*.sbd"
#TBD
echo "Getting ramses tbd files..."
cd /data/gandalf/deployments/skio/ramses/binary_files/tbd
wget -q -r -l1 -nH --cut-dirs=4 http://dockserver.skio.uga.edu/gmc/gliders/ramses/from-glider/ -A "ramses-2018-*.tbd"

