#!/bin/bash
docker exec -e COLUMNS="`tput cols`" -e LINES="`tput lines`" -ti tools /bin/bash
