#!/bin/bash

for i in daq9 daq10 daq12 daq13
do
    ansible-playbook $i.yml 
done
