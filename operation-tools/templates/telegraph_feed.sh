#!/bin/bash

if [ $# -ne 1 ]
then
    echo "Usage   : $0 DETECTOR"
    echo "Example : $0 JF06T32V02"
    exit
fi

DETECTOR=$1
DS=`echo ${DETECTOR} | cut -c 3-4`

if [ ${DETECTOR} == JF06T08V04 ]
then
    DS=06_4M
fi

NM=`echo ${DETECTOR} | cut -c 6-7`

NM=`expr ${NM} - 1`

for SERVICE in udp_recv buffer_writer
do
    for m in `seq -w 00 ${NM}`
    do
         journalctl -u JF${DS}-${SERVICE}-worker@${m} -n 1 | tail -1 | awk -F ': ' '{print $2}' | sed 's/-/_/g' | grep "^jf"
    done
done

journalctl -u JF${DS}-stream2vis -n 1 | tail -1 | awk -F ': ' '{print $2}' | sed 's/-/_/g' | grep "^sf"

exit 0
