from copy import deepcopy
from logging import getLogger
from random import randint
from time import sleep, time

import requests

from sf_daq_broker import config

_logger = getLogger("broker_writer")


def get_data_api_request(channels, start_pulse_id, stop_pulse_id):
    return {
        "channels": [{"name": ch, "backend": config.IMAGE_BACKEND if ch.endswith(":FPICTURE") else config.DATA_BACKEND}
                     for ch in channels],
        "range": {
            "startPulseId": start_pulse_id,
            "endPulseId": stop_pulse_id},
        "response": {
            "format": "json",
            "compression": "none"},
        "eventFields": ["channel", "pulseId", "value", "shape", "globalDate"],
        "configFields": ["type", "shape"]
    }


def get_writer_request(writer_type, channels, output_file, metadata, start_pulse_id, stop_pulse_id, run_log_file):

    return {
        "writer_type": writer_type,
        "channels": channels,

        "start_pulse_id": start_pulse_id,
        "stop_pulse_id": stop_pulse_id,

        "output_file": output_file,
        "run_log_file": run_log_file,

        "metadata": metadata,
        "timestamp": time()
    }


def transform_range_from_pulse_id_to_timestamp(data_api_request):

    new_data_api_request = deepcopy(data_api_request)

    try:

        mapping_request = {"range": {"startPulseId": data_api_request["range"]["startPulseId"],
                                     "endPulseId": data_api_request["range"]["endPulseId"]+1}}


        mapping_response = requests.post(url=config.DATA_API_QUERY_ADDRESS + "/mapping", json=mapping_request, timeout=10).json()
        _logger.info(f"Response to mapping request: {mapping_response}")

        del new_data_api_request["range"]["startPulseId"]
        new_data_api_request["range"]["startSeconds"] = mapping_response[0]["start"]["globalSeconds"]

        del new_data_api_request["range"]["endPulseId"]
        new_data_api_request["range"]["endSeconds"] = mapping_response[0]["end"]["globalSeconds"]

#        _logger.info(f"Transformed request to startSeconds and endSeconds. {new_data_api_request}")

    except Exception as e:
        _logger.error(e)
        raise RuntimeError("Cannot retrieve the pulse_id to timestamp mapping.") from e

    return new_data_api_request

def pulse_id_to_seconds(pulse_id):

    sec = 0
    try:
        request = requests.get(f"{config.PULSEID2SECONDS_MATCHING_ADDRESS}/{pulse_id}")
        if request.status_code == 200:
            sec = float(request.json())/1000000000.
        else:
            _logger.error(f"Problem to convert {pulse_id} to timestamp. return code {request.status_code}")
            _logger.error(f"Trying second time")
            sleep(30)
            request = requests.get(f"{config.PULSEID2SECONDS_MATCHING_ADDRESS}/{pulse_id}")
            if request.status_code == 200:
                sec = float(request.json())/1000000000.
            else:
                _logger.error(f"Problem(second time) to convert {pulse_id} to timestamp. return code {request.status_code}")
    except Exception as e:
        _logger.error(e)
        raise RuntimeError("Cannot convert pulse_id to time")
    return sec

def pulse_id_to_timestamp(pulse_id):

    ts = 0
    try:
        sleep(randint(1,10))
        request = requests.get(f"{config.PULSEID2SECONDS_MATCHING_ADDRESS}/{pulse_id}")
        if request.status_code == 200:
            ts = request.json()
        else:
            _logger.error(f"Problem to convert {pulse_id} to timestamp. return code {request.status_code}")
            _logger.error(f"Trying second time")
            sleep(randint(1,10))
            request = requests.get(f"{config.PULSEID2SECONDS_MATCHING_ADDRESS}/{pulse_id}")
            if request.status_code == 200:
                ts = request.json()
            else:
                _logger.error(f"Problem(second time) to convert {pulse_id} to timestamp. return code {request.status_code}")
    except Exception as e:
        _logger.error(e)
        raise RuntimeError("Cannot convert pulse_id to time")
    return ts

def transform_range_from_pulse_id_to_timestamp_new(data_api_request):

    new_data_api_request = deepcopy(data_api_request)

    try:
        start_ts = pulse_id_to_timestamp(data_api_request["range"]["startPulseId"])
        stop_ts  = pulse_id_to_timestamp(data_api_request["range"]["endPulseId"]+1)

        if start_ts != 0 and stop_ts != 0 and start_ts < stop_ts:
            del new_data_api_request["range"]["startPulseId"]
            new_data_api_request["range"]["startTS"] = start_ts
            del new_data_api_request["range"]["endPulseId"]
            new_data_api_request["range"]["endTS"] = stop_ts
        else:
            _logger.error(f"Convertion pulse_id to time failed {start_ts} {stop_ts}")

    except Exception as e:
        _logger.error(e)
        raise RuntimeError("Failed to convert pulse_id to time")

    return new_data_api_request
