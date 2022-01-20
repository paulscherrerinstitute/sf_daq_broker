#!/bin/bash

SERVICE_NAME=sf.{{ item.beamline_name }}.epics_buffer
SERVICE_VERSION=1.1.2
REDIS_HOST=127.0.0.1
CONFIG=/home/dbe/service_configs/sf.{{ item.beamline_name }}.epics_buffer.json

touch ${CONFIG}

/home/dbe/service_scripts/check_config_changed.sh ${CONFIG} sf.{{ item.beamline_name }}.epics_buffer &

taskset -c {{ item.buffer_cores }} \
docker run --rm --net=host \
	--name="${SERVICE_NAME}" \
	-e SERVICE_NAME="${SERVICE_NAME}" \
	-e REDIS_HOST="${REDIS_HOST}" \
	-e EPICS_CA_ADDR_LIST=sf-daq-cagw.psi.ch:5062 \
	-v "${CONFIG}":/std_daq_service/config.json \
	docker.io/paulscherrerinstitute/std-daq-service:"${SERVICE_VERSION}" \
	epics_buffer

