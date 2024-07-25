#!/bin/bash
echo "Harvesting .nc files for sg658"
cd /data/gandalf/deployments/uri/sg658/binary_files/nc
rsync -avp rcurrier@52.4.19.192:/home2/sg658/p658*.nc .
echo "Harvest complete for sg658"
cd /home/rdc/src/gandalf
