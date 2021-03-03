#!/bin/bash

coreAssociated="{{ cores_assembler }}"
CONFIG={{ detector_config }}
#SERVICE={{ detector }}-assembler

#/home/dbe/service_scripts/check_config_changed.sh ${CONFIG} ${SERVICE} &

taskset -c ${coreAssociated} /home/dbe/bin/jf_assembler ${CONFIG}

