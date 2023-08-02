#!/bin/bash

source /sf/jungfrau/applications/miniconda3/etc/profile.d/conda.sh
conda deactivate
conda activate sf-dap

CORE={{ dap_accumulator_cores }}

taskset -c ${CORE} python /sf/jungfrau/applications/sf-dap/code/accumulator.py --accumulator {{ dap_accumulator_host }} --accumulator_port {{ dap_accumulator_port }}
