#!/bin/bash

if [ $# != 1 ]
then
    echo Usage : $0 DETECTOR_NAME
    echo Example : $0 JF01T03V01
    exit
fi

DETECTOR=$1

export PATH=/home/dbe/miniconda3/bin:$PATH
source /home/dbe/miniconda3/etc/profile.d/conda.sh
conda deactivate
conda activate detector

python initialise_detector.py --detector ${DETECTOR}
