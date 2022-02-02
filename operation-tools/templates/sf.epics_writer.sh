#!/bin/bash

SERVICE_NAME=sf.{{ item.beamline_name }}.epics_writer
SERVICE_VERSION={{ epics_buffer_container_version }}
REDIS_HOST=127.0.0.1
BROKER_HOST=127.0.0.1

# start redis docker, if it's not running
/home/dbe/service_scripts/sf-redis.start.sh

taskset -c {{ item.writer_cores }} \
docker run --rm --net=host \
	--name="${SERVICE_NAME}" \
	-e SERVICE_NAME="${SERVICE_NAME}" \
	-e BROKER_HOST="${BROKER_HOST}" \
	-e REDIS_HOST="${REDIS_HOST}" \
	-v /sf/{{ item.beamline_name }}/data:/sf/{{ item.beamline_name }}/data \
	docker.io/paulscherrerinstitute/std-daq-service:"${SERVICE_VERSION}" \
	epics_writer

