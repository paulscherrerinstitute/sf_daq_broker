#!/bin/bash

if [ $# != 1 ]
then
    systemctl start sf-daq_writer@{01..{{ number_of_writers}}}
    exit
fi

export EPICS_CA_ADDR_LIST=sf-daq-cagw.psi.ch:5062

source /home/dbe/miniconda3/etc/profile.d/conda.sh
conda deactivate
conda activate sf-daq

M=$1

taskset -c $M python /home/dbe/git/sf_daq_broker/sf_daq_broker/writer/start.py  --writer_id $M    
