#!/bin/bash
echo "Started run at: " 
date
#TAMU 541
echo "Harvesting TAMU Sverdrup"
echo "Getting log files..."
cd /data/gandalf/deployments/tamu/unit_541/ascii_files/logs
wget -q -r -l1 -nH --cut-dirs=3  http://tabs-os.gerg.tamu.edu/~woody/glider_541/  -A "unit_541_network_net_0_2020*.log"
echo "Getting sbd files..."
cd /data/gandalf/deployments/tamu/unit_541/binary_files/sbd
wget -q -r -l1 -nH --cut-dirs=3  http://tabs-os.gerg.tamu.edu/~woody/glider_541/  -A "unit_541-2020*.sbd"
echo "Getting tbd files..."
cd /data/gandalf/deployments/tamu/unit_541/binary_files/tbd
wget -q -r -l1 -nH --cut-dirs=3  http://tabs-os.gerg.tamu.edu/~woody/glider_541/  -A "unit_541-2020*.tbd"
