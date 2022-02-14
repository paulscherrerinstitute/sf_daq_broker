#!/bin/bash

SERVICE_NAME=sf.{{ item.beamline_name }}.epics_writer
SERVICE_VERSION={{ epics_buffer_container_version }}
REDIS_HOST=127.0.0.1
REDIS_PORT={{ item.redis_port }}
BROKER_HOST=127.0.0.1

# start redis docker, if it's not running
/home/dbe/service_scripts/sf-redis.start.sh {{ item.beamline_name }} ${REDIS_PORT}

taskset -c {{ item.writer_cores }} \
docker run --rm --net=host \
	--name="${SERVICE_NAME}" \
	-e SERVICE_NAME="${SERVICE_NAME}" \
	-e BROKER_HOST="${BROKER_HOST}" \
	-e REDIS_HOST="${REDIS_HOST}" \
        -e REDIS_PORT="${REDIS_PORT}" \
	-v /sf/{{ item.beamline_name }}/data:/sf/{{ item.beamline_name }}/data \
        -v /gpfs/photonics/swissfel/raw/{{ item.beamline_name }}-staff:/gpfs/photonics/swissfel/raw/{{ item.beamline_name }}-staff \
        -v /gpfs/photonics/swissfel/raw/{{ item.beamline_name }}:/gpfs/photonics/swissfel/raw/{{ item.beamline_name }} \
	docker.io/paulscherrerinstitute/std-daq-service:"${SERVICE_VERSION}" \
	epics_writer \
        --tag epics_{{ item.beamline_name }}

