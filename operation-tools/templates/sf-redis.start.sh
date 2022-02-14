#!/bin/bash

if [ $# != 2 ]
then
    echo "Usage: $0 <beamline> <port>"
    echo "example: $0 alvra 6000"
    echo "Not enough input provided, exit"
    exit
fi

BEAMLINE=$1
PORT=$2

docker ps -a | grep redis-${BEAMLINE} > /dev/null
if [ $? != 0 ]
then
    docker run -d --rm --name redis-${BEAMLINE} --net=bridge -p ${PORT}:6379 redis redis-server --save ''
else
    docker ps -a | grep redis-${BEAMLINE} | grep " Up " > /dev/null
    if [ $? != 0 ]
    then
        docker start redis-${BEAMLINE}
    fi
fi
