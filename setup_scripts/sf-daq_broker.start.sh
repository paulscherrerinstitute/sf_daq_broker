#!/bin/bash

export PATH=/home/dbe/miniconda3/bin:$PATH

source /home/dbe/miniconda3/etc/profile.d/conda.sh

conda deactivate
conda activate sf-daq

taskset -c 0 python /home/dbe/git/sf_daq_broker/sf_daq_broker/broker.py 
