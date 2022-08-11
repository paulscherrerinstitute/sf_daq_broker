#!/bin/bash

source /home/dbe/miniconda3/etc/profile.d/conda.sh
conda deactivate
conda activate sf-daq

taskset -c 1 python /home/dbe/git/sf_daq_broker/sf_daq_broker/broker_manager_slow.py
