#!/bin/bash

if [ $# != 1 ]
then
    systemctl start {{ detector }}-buffer-worker@{00..{{ number_modules}}}
    exit
fi

M=$1

coreAssociatedBuffer=({{ cores_receivers }})

initialUDPport={{ initial_udp_port }}
port=$((${initialUDPport}+10#${M}))
DETECTOR={{ detector_full_name }}

taskset -c ${coreAssociatedBuffer[10#${M}]} /usr/local/bin/sf_buffer ${DETECTOR} M${M} ${port} /gpfs/photonics/swissfel/buffer/${DETECTOR} ${M}

