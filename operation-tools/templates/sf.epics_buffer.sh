#!/bin/bash

SERVICE_NAME=sf.{{ item.beamline_name }}.epics_buffer
SERVICE_VERSION={{ epics_buffer_container_version }}
REDIS_HOST=127.0.0.1
REDIS_PORT={{ item.redis_port }}
CONFIG=/home/dbe/service_configs/sf.{{ item.beamline_name }}.epics_buffer.json

# start redis docker, if it's not running
/home/dbe/service_scripts/sf-redis.start.sh {{ item.beamline_name }} ${REDIS_PORT}

if [ ! -f ${CONFIG} ]
then
    cat <<EOF > ${CONFIG}
{
  "pulse_id_pv": "SLAAR11-LTIM01-EVR0:RX-PULSEID",
  "pv_list": []
}
EOF

fi

/home/dbe/service_scripts/check_config_changed.sh ${CONFIG} sf.{{ item.beamline_name }}.epics_buffer &

taskset -c {{ item.buffer_cores }} \
docker run --rm --net=host \
	--name="${SERVICE_NAME}" \
	-e SERVICE_NAME="${SERVICE_NAME}" \
	-e REDIS_HOST="${REDIS_HOST}" \
        -e REDIS_PORT="${REDIS_PORT}" \
	-e EPICS_CA_ADDR_LIST=sf-daq-cagw.psi.ch:5062 \
	-v "${CONFIG}":/std_daq_service/config.json \
	docker.io/paulscherrerinstitute/std-daq-service:"${SERVICE_VERSION}" \
	epics_buffer \
	--log_level {{ epics_buffer_log_level }}

