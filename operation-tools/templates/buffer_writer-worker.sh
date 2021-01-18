#!/bin/bash

if [ $# != 1 ]
then
    systemctl start {{ detector }}-buffer_writer-worker@{00..{{ last_module_number}}}
    exit
fi

M=$1

coreAssociatedBuffer=({{ cores_buffer_writer }})

taskset -c ${coreAssociatedBuffer[10#${M}]} /home/dbe/bin/jf_buffer_writer {{ detector_config }} ${M}

