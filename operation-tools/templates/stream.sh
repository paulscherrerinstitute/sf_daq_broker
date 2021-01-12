#!/bin/bash

coreAssociated="{{ stream_cores }}"
CONFIG=/gpfs/photonics/swissfel/buffer/config/{{ stream_config }}
SERVICE={{ detector }}-stream

/home/dbe/git/sf_daq_buffer/scripts/check_config_changed.sh ${CONFIG} ${SERVICE} &

taskset -c ${coreAssociated} /usr/local/bin/sf_stream ${CONFIG}

