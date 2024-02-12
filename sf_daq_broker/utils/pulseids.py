import logging
from copy import deepcopy
from random import randint
from time import sleep

import requests

from sf_daq_broker import config


_logger = logging.getLogger("broker_writer")



#def transform_range_from_pulse_id_to_timestamp(data_api_request):
#    new_data_api_request = deepcopy(data_api_request)

#    try:
#        start_pid = data_api_request["range"]["startPulseId"]
#        stop_pid  = data_api_request["range"]["endPulseId"] + 1

#        mapping_request = {
#            "range": {
#                "startPulseId": start_pid,
#                "endPulseId":   stop_pid
#            }
#        }

#        response = requests.post(url=config.DATA_API_QUERY_ADDRESS + "/mapping", json=mapping_request, timeout=10).json()
#        _logger.info(f"response to pulse IDs to timestamps mapping request: {response}")

#        del new_data_api_request["range"]["startPulseId"]
#        new_data_api_request["range"]["startSeconds"] = response[0]["start"]["globalSeconds"]

#        del new_data_api_request["range"]["endPulseId"]
#        new_data_api_request["range"]["endSeconds"] = response[0]["end"]["globalSeconds"]

##        _logger.info(f"transformed request in pulse IDs ({data_api_request}) to seconds ({new_data_api_request})")

#    except Exception as e:
#        _logger.error(f"mapping pulse IDs to timestamps failed: {e}")
#        raise RuntimeError(f"mapping pulse IDs to timestamps failed (due to: {e})") from e

#    return new_data_api_request


def pulse_id_to_seconds(pulse_id):
    sec = 0

    try:
        request = requests.get(f"{config.PULSEID2SECONDS_MATCHING_ADDRESS}/{pulse_id}")
        if request.status_code == 200:
            sec = float(request.json()) / 1000000000.
        else:
            _logger.error(f"mapping pulse ID {pulse_id} to timestamp failed: status code {request.status_code} -- retrying")
            sleep(30)
            request = requests.get(f"{config.PULSEID2SECONDS_MATCHING_ADDRESS}/{pulse_id}")
            if request.status_code == 200:
                sec = float(request.json()) / 1000000000.
            else:
                _logger.error(f"mapping pulse ID {pulse_id} to timestamp failed again: status code {request.status_code}")

    except Exception as e:
        _logger.error(f"mapping pulse ID {pulse_id} to timestamp failed: {e}")
        raise RuntimeError(f"mapping pulse ID {pulse_id} to timestamp failed (due to: {e})") from e

    return sec


def pulse_id_to_timestamp(pulse_id):
    ts = 0

    try:
        sleep(randint(1, 10))
        request = requests.get(f"{config.PULSEID2SECONDS_MATCHING_ADDRESS}/{pulse_id}")
        if request.status_code == 200:
            ts = request.json()
        else:
            _logger.error(f"mapping pulse ID {pulse_id} to timestamp failed: status code {request.status_code} -- retrying")
            sleep(randint(1, 10))
            request = requests.get(f"{config.PULSEID2SECONDS_MATCHING_ADDRESS}/{pulse_id}")
            if request.status_code == 200:
                ts = request.json()
            else:
                _logger.error(f"mapping pulse ID {pulse_id} to timestamp failed again: status code {request.status_code}")

    except Exception as e:
        _logger.error(f"mapping pulse ID {pulse_id} to timestamp failed: {e}")
        raise RuntimeError(f"mapping pulse ID {pulse_id} to timestamp failed (due to: {e})") from e

    return ts


def transform_range_from_pulse_id_to_timestamp_new(data_api_request):
    new_data_api_request = deepcopy(data_api_request)

    try:
        start_pid = data_api_request["range"]["startPulseId"]
        stop_pid  = data_api_request["range"]["endPulseId"] + 1

        start_ts = pulse_id_to_timestamp(start_pid)
        stop_ts  = pulse_id_to_timestamp(stop_pid)

        if start_ts != 0 and stop_ts != 0 and start_ts < stop_ts:
            del new_data_api_request["range"]["startPulseId"]
            new_data_api_request["range"]["startTS"] = start_ts
            del new_data_api_request["range"]["endPulseId"]
            new_data_api_request["range"]["endTS"] = stop_ts
        else:
            _logger.error(f"mapping pulse IDs (start_pid, stop_pid) to timestamps failed: ({start_ts}, {stop_ts})")

    except Exception as e:
        _logger.error(f"mapping pulse IDs to timestamps failed: {e}")
        raise RuntimeError(f"mapping pulse IDs to timestamps failed (due to: {e})") from e

    return new_data_api_request



