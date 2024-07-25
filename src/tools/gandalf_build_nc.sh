#!/bin/bash
cd /opt/gncutils/scripts
./dba_to_ngdac_profile_nc.py -c \
/data/gandalf/gandalf_configs/vehicles/$2/ngdac \
/data/gandalf/deployments/$1/$2/processed_data/dba/merged/*.dba \
-o /data/gandalf/deployments/$1/$2/processed_data/ngdac_files
