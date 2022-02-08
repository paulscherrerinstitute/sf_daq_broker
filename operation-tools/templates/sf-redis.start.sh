#!/bin/bash

docker ps -a | grep redis > /dev/null
if [ $? != 0 ]
then
    docker run -d --rm --name redis --net=bridge -p 6379:6379 redis redis-server --save ''
else
    docker ps -a | grep redis | grep " Up " > /dev/null
    if [ $? != 0 ]
    then
        docker start redis
    fi
fi
