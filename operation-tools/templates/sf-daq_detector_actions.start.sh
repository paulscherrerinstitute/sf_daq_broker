#!/bin/bash

if [ $# != 1 ]
then
    systemctl start sf-daq_detector_actions_worker@{01..{{ number_of_detector_actions_workers}}}
    exit
fi

export EPICS_CA_ADDR_LIST=sf-daq-cagw.psi.ch:5062

source /home/dbe/miniconda3/etc/profile.d/conda.sh
conda deactivate
conda activate sf-daq

M=$1
C={{ detector_actions_cores }}

export OMP_NUM_THREADS=1

taskset -c $C python /home/dbe/git/sf_daq_broker/sf_daq_broker/writer/start.py  --writer_id $M  --writer_type 3
