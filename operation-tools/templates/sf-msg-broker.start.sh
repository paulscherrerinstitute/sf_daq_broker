#!/bin/bash

docker ps -a | grep sf-msg-broker > /dev/null
if [ $? != 0 ]
then
    docker run -d --hostname {{ansible_hostname}} --name sf-msg-broker --net=host rabbitmq:3-management
else
    docker ps -a | grep sf-msg-broker | grep " Up " > /dev/null
    if [ $? != 0 ]
    then
        docker start sf-msg-broker
    fi
fi
