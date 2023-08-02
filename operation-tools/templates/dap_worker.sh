#!/bin/bash

CORES=({{ dap_worker_cores }})
NW={{ dap_worker_cores.split() | length }} 

if [ $# != 1 ]
then
    for i in `seq 1 ${NW}`
    do
        echo "Starting worker $i"
        systemctl start {{ detector }}-dap_worker@$i
    done
    exit
fi

source /sf/jungfrau/applications/miniconda3/etc/profile.d/conda.sh
conda deactivate
conda activate sf-dap

CP=`expr $1 - 1`
if [ ${CP} -lt 0 ] || [ ${CP} -ge ${NW} ]
then
    echo "Error, not prepared worker number $1 (${CP} position in array), number of workers: ${NW}"
    exit
fi
CORE=${CORES[${CP}]}

taskset -c ${CORE} python /sf/jungfrau/applications/sf-dap/code/worker.py --backend {{ dap_data_stream }} --accumulator {{ dap_accumulator_host }} --accumulator_port {{ dap_accumulator_port }} --visualisation {{ dap_visualisation_host }} --visualisation_port {{ dap_to_visualisation }} --peakfinder_parameters {{ dap_parameters_file }} --skip_frames_rate {{ dap_skip_frames }}

