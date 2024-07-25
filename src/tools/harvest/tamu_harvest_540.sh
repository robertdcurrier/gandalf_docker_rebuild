#!/bin/bash
echo "Started run at: " 
date
#TAMU 541
echo "Harvesting TAMU Stommel"
echo "Getting log files..."
cd /data/gandalf/deployments/tamu/unit_540/ascii_files/logs
wget  -q -r -l1 -nH --cut-dirs=3  http://tabs-os.gerg.tamu.edu/~woody/glider_540/  -A "unit_540_network_net_0_2020*.log"
echo "Getting sbd files..."
cd /data/gandalf/deployments/tamu/unit_540/binary_files/sbd
wget  -q -r -l1 -nH --cut-dirs=3  http://tabs-os.gerg.tamu.edu/~woody/glider_540/  -A "unit_540-2020*.sbd"
echo "Getting tbd files..."
cd /data/gandalf/deployments/tamu/unit_540/binary_files/tbd
wget -q -r -l1 -nH --cut-dirs=3  http://tabs-os.gerg.tamu.edu/~woody/glider_540/  -A "unit_540-2020*.tbd"
