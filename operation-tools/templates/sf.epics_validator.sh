#!/bin/bash

SERVICE_NAME=sf.{{ item.beamline_name }}.epics_validator
SERVICE_VERSION={{ epics_buffer_container_version }}
REDIS_HOST=127.0.0.1
REDIS_PORT={{ item.redis_port }}
BROKER_HOST=127.0.0.1

taskset -c {{ item.validator_cores }} \
docker run --rm --net=host \
	--name="${SERVICE_NAME}" \
	-e SERVICE_NAME="${SERVICE_NAME}" \
	-e BROKER_HOST="${BROKER_HOST}" \
	-e REDIS_HOST="${REDIS_HOST}" \
        -e REDIS_PORT="${REDIS_PORT}" \
	-v /sf/{{ item.beamline_name }}/data:/sf/{{ item.beamline_name }}/data \
        -v /gpfs/photonics/{{ item.beamline_storage }}/raw/{{ item.beamline_name }}-staff:/gpfs/photonics/{{ item.beamline_storage }}/raw/{{ item.beamline_name }}-staff \
        -v /gpfs/photonics/{{ item.beamline_storage }}/raw/{{ item.beamline_name }}:/gpfs/photonics/{{ item.beamline_storage }}/raw/{{ item.beamline_name }} \
	docker.io/paulscherrerinstitute/std-daq-service:"${SERVICE_VERSION}" \
	epics_validator \
        sf.{{ item.beamline_name }}.epics_writer
	--log_level {{ epics_buffer_log_level }}

