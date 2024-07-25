#!/bin/bash
# 2024-06-26 rdc updated to run via newgrp

echo "gandalf_mcp.sh master control script"

# First we harvest
echo "HARVESTING"
/home/rdc/src/gandalf/src/tools/gandalf_slocum_harvest.py
/home/rdc/src/gandalf/src/tools/gandalf_sg_harvest.py

echo "ARGO"
# ARGO

echo "GANDALF UGOS Floats"
#docker exec tools /gandalf/tools/gandalf_ugos_floats.py

echo "SEATREC"
# Seatrec -- disabled 2023-09-19 as URL broken
# restored on 2023-10-26 with new URL
#docker exec tools /gandalf/tools/gandalf_seatrec_DIM.py

echo "SAILDRONE"
# Saildrone
#docker exec tools /gandalf/tools/gandalf_to_saildrone.py

echo "GNC UTILS"
# GNC Utils -- need to iterate deployed Slocums -- for now we manually call
#docker exec gncutils /gandalf/tools/gandalf_build_nc.sh alaska unit_191
#docker exec gncutils /gandalf/tools/gandalf_build_nc.sh tamu unit_307
#docker exec gncutils /gandalf/tools/gandalf_build_nc.sh tamu unit_308
#docker exec gncutils /gandalf/tools/gandalf_build_nc.sh usf usf-bass
#docker exec gncutils /gandalf/tools/gandalf_build_nc.sh mote mote-genie
#docker exec gncutils /gandalf/tools/gandalf_build_nc.sh usf usf-gansett
#docker exec gncutils /gandalf/tools/gandalf_build_nc.sh skio franklin
#docker exec gncutils /gandalf/tools/gandalf_build_nc.sh usf usf-stella
#docker exec gncutils /gandalf/tools/gandalf_build_nc.sh louisiana sedna
#docker exec gncutils /gandalf/tools/gandalf_build_nc.sh skio unit_1091
#docker exec gncutils /gandalf/tools/gandalf_build_nc.sh usf usf-sam
#docker exec gncutils /gandalf/tools/gandalf_build_nc.sh tamu unit_541
#docker exec gncutils /gandalf/tools/gandalf_build_nc.sh usf usf-jaialai
#docker exec gncutils /gandalf/tools/gandalf_build_nc.sh mote mote-dora
#docker exec gncutils /gandalf/tools/gandalf_build_nc.sh mote mote-SeaXplorer
#docker exec gncutils /gandalf/tools/gandalf_build_nc.sh usf usf-sam
#docker exec gncutils /gandalf/tools/gandalf_build_nc.sh mote mote-SeaXplorer
docker exec gncutils /gandalf/tools/gandalf_build_nc.sh tamu unit_307
docker exec gncutils /gandalf/tools/gandalf_build_nc.sh tamu unit_1148
docker exec gncutils /gandalf/tools/gandalf_build_nc.sh mote mote-dora
docker exec gncutils /gandalf/tools/gandalf_build_nc.sh usf usf-sam
echo "GANDALF_MP_MCP"
docker exec tools /gandalf/tools/gandalf_MP_mcp.py
