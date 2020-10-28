#!/bin/bash

export PATH=/home/dbe/miniconda3/bin:$PATH

source /home/dbe/miniconda3/etc/profile.d/conda.sh

conda deactivate
conda activate sf-daq

M=$1

taskset -c $M python /home/dbe/git/sf_daq_broker/sf_daq_broker/writer/start.py  --writer_id $M    
