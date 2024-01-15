import logging
from datetime import datetime
from random import randrange
from time import time

import h5py
import numpy
import pytz

from sf_daq_broker import config, utils

_logger = logging.getLogger("broker_writer")


def tsfmt(ts):
    ts = ts // 1000
    n = ts // 1000000
    m = ts % 1000000
    s = datetime.fromtimestamp(n).astimezone(pytz.timezone("UTC")).strftime("%Y-%m-%dT%H:%M:%S")
    s = f"{s}.{m:06d}Z"
    return s

def check_data_consistency(start_pulse_id, stop_pulse_id, rate_multiplicator, channels, output_file):

    start_check_time = time()

    # run checks
    expected_pulse_id = []
    for p in range(start_pulse_id,stop_pulse_id+1):
        if p%rate_multiplicator == 0:
            expected_pulse_id.append(p)
    expected_pulse_id = numpy.array(expected_pulse_id)
    expected_number_measurements = len(expected_pulse_id)

    try:
        data_h5py = h5py.File(output_file,"r")
        inside_file = list(data_h5py.keys())
        for channel in channels:
            if channel not in inside_file:
                _logger.error(f"check {channel} not present in file")
            else:

                pulse_id_raw    = data_h5py[f"/{channel}/pulse_id"][:]

                if numpy.sum(pulse_id_raw < start_pulse_id) or numpy.sum(pulse_id_raw > stop_pulse_id):
                    _logger.error(f"check {channel} contains pulse_id outside of requested range")

                n_pulse_id_raw = len(pulse_id_raw)

                n_unique_pulse_id_raw = len(set(pulse_id_raw))

                duplicated_entries = False
                if n_pulse_id_raw != n_unique_pulse_id_raw:
                    duplicated_entries = True
                    _logger.error(f"check {channel} contains duplicated entries. Total entries : {n_pulse_id_raw}, duplicated entries : {n_pulse_id_raw-n_unique_pulse_id_raw} ")

                pulse_id = numpy.intersect1d(expected_pulse_id, pulse_id_raw)
                n_pulse_id = len(pulse_id)

                if n_pulse_id != expected_number_measurements:
                    _logger.error(f"check {channel} number of pulse_id(unique) is different from expected : {n_pulse_id} vs {expected_number_measurements}")
                else:
                    if pulse_id[0] != expected_pulse_id[0] or pulse_id[-1] != expected_pulse_id[-1]:
                        _logger.error(f"check {channel} start/stop pulse_id are not the one which are requested (requested : {expected_pulse_id[0]},{expected_pulse_id[-1]}, got: {pulse_id[0]},{pulse_id[-1]}) ")
                        if not duplicated_entries:
                            pulse_id_check = True
                            for i in range(n_pulse_id):
                                if pulse_id[i] != expected_pulse_id[i]:
                                    pulse_id_check = False
                            if not pulse_id_check:
                                _logger.error(f"check {channel} pulse_id are not monotonic")

    except Exception as e:
        _logger.error("check failed")
        _logger.error(e)

    time_delta = time() - start_check_time
    _logger.info(f"Check of data consistency took {time_delta} seconds.")


def write_from_imagebuffer(data_api_request, output_file, _parameters):
    import data_api3.h5 as h5

    start_pulse_id = data_api_request["range"]["startPulseId"]
    stop_pulse_id  = data_api_request["range"]["endPulseId"]
    rate_multiplicator = data_api_request.get("rate_multiplicator", 1)

    _logger.debug(f"Data API request: {data_api_request}")

    data_api_request_timestamp = utils.transform_range_from_pulse_id_to_timestamp_new(data_api_request)

    channels = [channel["name"] for channel in data_api_request_timestamp["channels"]]

    if "startTS" not in data_api_request_timestamp["range"]:
        _logger.info("startTS not present, tranformation of pulseid to timestamp failed")
        return

    start = tsfmt(data_api_request_timestamp["range"]["startTS"])
    end = tsfmt(data_api_request_timestamp["range"]["endTS"])

    query = {
        "channels": channels,
        "range": {
            "type": "date",
            "startDate": start,
            "endDate": end
        }
    }

    image_buffer_url = config.IMAGE_API_QUERY_ADDRESS[randrange(len(config.IMAGE_API_QUERY_ADDRESS))]

    _logger.debug(f'Requesting "{query}" to output_file {output_file} from {image_buffer_url}')

    start_time = time()

    try:
        _logger.debug(f"query request : {query} {output_file} {image_buffer_url}")
        h5.request(query, output_file, url=image_buffer_url)
        delta_time = time() - start_time
        _logger.info(f"Image download and writing took {delta_time} seconds.")
    except Exception as e:
        _logger.error("Got exception from data_api3")
        _logger.error(e)

    check_data_consistency(start_pulse_id, stop_pulse_id, rate_multiplicator, channels, output_file)

def write_from_databuffer_api3(data_api_request, output_file, _parameters):
    import data_api3.h5 as h5

    _logger.debug(f"Data3 API request: {data_api_request}")

    start_pulse_id = data_api_request["range"]["startPulseId"]
    stop_pulse_id  = data_api_request["range"]["endPulseId"]
    rate_multiplicator = data_api_request.get("rate_multiplicator", 1)

    data_api_request_timestamp = utils.transform_range_from_pulse_id_to_timestamp_new(data_api_request)

    channels = [channel["name"] for channel in data_api_request_timestamp["channels"]]

    if "startTS" not in data_api_request_timestamp["range"]:
        _logger.info("startTS not present, tranformation of pulseid to timestamp failed")
        return

    start = tsfmt(data_api_request_timestamp["range"]["startTS"])
    end = tsfmt(data_api_request_timestamp["range"]["endTS"])

    query = {
        "channels": channels,
        "range": {
            "type": "date",
            "startDate": start,
            "endDate": end
        }
    }

    data_buffer_url = config.DATA_API3_QUERY_ADDRESS

    _logger.debug(f'Requesting "{query}" to output_file {output_file} from {data_buffer_url}')

    start_time = time()

    try:
        h5.request(query, filename=output_file, baseurl=data_buffer_url, default_backend=config.DATA_BACKEND)
        delta_time = time() - start_time
        _logger.info(f"Data download and writing took {delta_time} seconds.")
    except Exception as e:
        _logger.error("Got exception from data_api3")
        _logger.error(e)

    check_data_consistency(start_pulse_id, stop_pulse_id, rate_multiplicator, channels, output_file)
