#!/bin/bash

if [ $# -ne 1 ]
then
    echo "Usage   : $0 DETECTOR"
    echo "Example : $0 JF06T32V02"
    exit
fi

DETECTOR=$1
DS=`echo ${DETECTOR} | cut -c 3-4`
NM=`echo ${DETECTOR} | cut -c 6-7`

NM=`expr ${NM} - 1`

#NM=01

for SERVICE in writer worker
do
    for m in `seq -w 00 ${NM}`
    do
         journalctl -u JF${DS}-buffer-${SERVICE}@${m} -n 1 | tail -1 | awk -F ': ' '{print $2}' | sed 's/-/_/g'
    done
done

