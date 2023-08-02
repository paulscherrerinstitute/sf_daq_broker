#!/bin/bash

source /home/dbe/miniconda3/etc/profile.d/conda.sh
conda deactivate
conda activate vis

PORT={{ visualisation_port }}
PORT_BACKEND={{ dap_to_visualisation }}

H=`echo ${HOSTNAME} | sed 's/.psi.ch//'`

CORES="{{ visualisation_cores }}"

taskset -c ${CORES} \
streamvis {{ visualisation_view }} \
--allow-websocket-origin=${H}:${PORT} --allow-websocket-origin=localhost:${PORT} \
--port=${PORT} \
--address  tcp://*:${PORT_BACKEND} --connection-mode bind \
--buffer-size 100 \
--page-title "dap: {{ visualisation_title }}"

