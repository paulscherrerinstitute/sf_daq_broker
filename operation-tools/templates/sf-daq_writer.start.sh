#!/bin/bash

if [ $# != 1 ]
then
    systemctl start sf-daq_writer@{00..{{ number_of_writers}}}
    exit
fi

source /home/dbe/miniconda3/etc/profile.d/conda.sh
conda deactivate
conda activate sf-daq

M=$1

taskset -c $M python /home/dbe/git/sf_daq_broker/sf_daq_broker/writer/start.py  --writer_id $M    
