#!/bin/bash
echo "Started run at: " 
date
#TAMU 307
echo "Harvesting TAMU glider_307"
echo "Getting log files..."
cd /data/gandalf/deployments/tamu/unit_307/ascii_files/logs
wget -q -r -l1 -nH --cut-dirs=3  http://tabs.gerg.tamu.edu/~woody/glider_307/  -A "unit_307_network_net_0_2019*.log"
echo "Getting sbd files..."
cd /data/gandalf/deployments/tamu/unit_307/binary_files/sbd
wget -q -r -l1 -nH --cut-dirs=3  http://tabs.gerg.tamu.edu/~woody/glider_307/  -A "unit_307-2019*.sbd"
echo "Getting tbd files..."
cd /data/gandalf/deployments/tamu/unit_307/binary_files/tbd
wget -q -r -l1 -nH --cut-dirs=3  http://tabs.gerg.tamu.edu/~woody/glider_307/  -A "unit_307-2019*.tbd"
