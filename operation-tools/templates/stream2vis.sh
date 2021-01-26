#!/bin/bash

coreAssociated="{{ stream2vis_cores }}"
#CONFIG=/gpfs/photonics/swissfel/buffer/config/{{ detector_config }}
CONFIG={{ detector_config }}
SERVICE={{ detector }}-stream2vis

/home/dbe/service_scripts/check_config_changed.sh ${CONFIG} ${SERVICE} &

taskset -c ${coreAssociated} /home/dbe/bin/sf_stream ${CONFIG} vis

