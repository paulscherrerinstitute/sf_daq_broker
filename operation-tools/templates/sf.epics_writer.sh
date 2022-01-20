#!/bin/bash

SERVICE_NAME=sf.{{ item.beamline_name }}.epics_writer
SERVICE_VERSION=1.1.4
REDIS_HOST=127.0.0.1
BROKER_HOST=127.0.0.1

taskset -c {{ item.writer_cores }} \
docker run --rm --net=host \
	--name="${SERVICE_NAME}" \
	-e SERVICE_NAME="${SERVICE_NAME}" \
	-e BROKER_HOST="${BROKER_HOST}" \
	-e REDIS_HOST="${REDIS_HOST}" \
	-v /gpfs/photonics/swissfel/develop/epics_writer:/data \
	docker.io/paulscherrerinstitute/std-daq-service:"${SERVICE_VERSION}" \
	epics_writer

