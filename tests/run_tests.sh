#!/bin/bash

dn=$(dirname $0)
cd "$dn/.."

PYTHONPATH=$PWD python -m unittest tests/test_broker.py


