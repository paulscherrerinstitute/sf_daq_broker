from copy import deepcopy
from logging import getLogger
from time import time

import requests

from sf_daq_broker import config

_logger = getLogger("broker_writer")


def get_data_api_request(channels, start_pulse_id, stop_pulse_id):
    return {
        "channels": [{'name': ch, 'backend': config.IMAGE_BACKEND if ch.endswith(":FPICTURE") else config.DATA_BACKEND}
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

        mapping_request = {'range': {'startPulseId': data_api_request["range"]["startPulseId"],
                                     'endPulseId': data_api_request["range"]["endPulseId"]+1}}

        mapping_response = requests.post(url=config.DATA_API_QUERY_ADDRESS + "/mapping", json=mapping_request, timeout=10).json()

        _logger.info("Response to mapping request: %s", mapping_response)

        del new_data_api_request["range"]["startPulseId"]
        new_data_api_request["range"]["startSeconds"] = mapping_response[0]["start"]["globalSeconds"]

        del new_data_api_request["range"]["endPulseId"]
        new_data_api_request["range"]["endSeconds"] = mapping_response[0]["end"]["globalSeconds"]

        _logger.info("Transformed request to startSeconds and endSeconds. %s" % new_data_api_request)

    except Exception as e:
        _logger.error(e)
        raise RuntimeError("Cannot retrieve the pulse_id to timestamp mapping.") from e

    return new_data_api_request

