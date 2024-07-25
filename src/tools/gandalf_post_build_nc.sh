#!/bin/bash
cd /opt/gncutils/scripts
./dba_to_ngdac_profile_nc.py \
/data/gandalf/gandalf_configs/$1/ngdac \
/data/gandalf/$2/processed_data/dba/merged/*.dba \
-o /data/gandalf/$2/processed_data/ngdac_files
