#!/bin/bash

if [ $# -lt 1 ]
then
    echo "Usage : $0 DETECTOR_NAME <number_of_cycles>"
    echo "           DETECTOR_NAME: JF07 or JF01..."
    echo "           number_of_cycles : optional, default 100"
    exit
fi

DETECTOR=$1
case ${DETECTOR} in
'JF01')
  D=1
  ;;
'JF02')
  D=2
  ;;
'JF06')
  D=6
  ;;
'JF07')
  D=7
  ;;
'JF13')
  D=13
  ;;
'JF11')
  D=11
  ;;
'JF04')
  D=4
  ;;
'JF03')
  D=3
  ;;
'JF09')
  D=9
  ;;
'JF10')
  D=10
  ;;
'JF10')
  D=10
  ;;
'JF14')
  D=14
  ;;
'JF15')
  D=15
  ;;
*)
  echo "Unsupported detector"
  exit
  ;;
esac

n_cycles=100
if [ $# == 2 ]
then
    n_cycles=$2
fi

export PATH=/home/dbe/miniconda3/bin:$PATH
source /home/dbe/miniconda3/etc/profile.d/conda.sh
conda activate sf-daq

sls_detector_put ${D}-stop
sls_detector_put ${D}-timing trigger
sls_detector_put ${D}-triggers ${n_cycles}
if [ ${DETECTOR} == "JF15" ]
then
  sls_detector_put ${D}-exptime 10us
else 
  sls_detector_put ${D}-exptime 5us
fi
sls_detector_put ${D}-frames 1
sls_detector_put ${D}-dr 16
#sls_detector_put ${D}-clearbit to 0x5d 0 # normal mode, not highG0
sls_detector_put ${D}-start

echo "Now start trigger"
