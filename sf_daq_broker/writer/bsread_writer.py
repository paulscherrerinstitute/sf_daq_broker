import logging
from datetime import datetime
from random import choice
from time import time

import h5py
import numpy as np
import pytz
from data_api3 import h5 as dapi3h5

from sf_daq_broker import config
from sf_daq_broker.utils import pulse_id_to_timestamp


_logger = logging.getLogger("broker_writer")



def write_from_imagebuffer(data_api_request, output_file, _parameters): #TODO: what is parameters for?
    buffer_url = choice(config.IMAGE_API_QUERY_ADDRESS)
    requester = lambda *args: dapi3h5.request(*args, url=buffer_url)
    what = "image"
    write_generic(data_api_request, output_file, buffer_url, requester, what)


def write_from_databuffer_api3(data_api_request, output_file, _parameters):
    buffer_url = config.DATA_API3_QUERY_ADDRESS
    requester = lambda *args: dapi3h5.request(*args, baseurl=buffer_url, default_backend=config.DATA_BACKEND)
    what = "data"
    write_generic(data_api_request, output_file, buffer_url, requester, what)


def write_generic(data_api_request, output_file, buffer_url, requester, what):
    _logger.debug(f"Data API 3 ({what} buffer) request: {data_api_request}")

    channels = data_api_request["channels"]
    channels = [channel["name"] for channel in channels]

    pid_range = data_api_request["range"]
    start_pid = pid_range["startPulseId"]
    stop_pid  = pid_range["endPulseId"] + 1

    try:
        start_ts = pulse_id_to_timestamp(start_pid)
        stop_ts  = pulse_id_to_timestamp(stop_pid)
    except RuntimeError:
        _logger.exception("request to Data API 3 to map pulse IDs to timestamps failed")
        raise

    start_ts = tsfmt(start_ts)
    stop_ts  = tsfmt(stop_ts)

    query = {
        "channels": channels,
        "range": {
            "type": "date",
            "startDate": start_ts,
            "endDate": stop_ts
        }
    }

    _logger.debug(f'requesting "{query}" from {buffer_url} to write to output file {output_file}')

    try:
        start_time = time()
        requester(query, output_file)
        delta_time = time() - start_time
        _logger.info(f"{what} download and writing took {delta_time} seconds")

    except Exception:
        _logger.exception("request to Data API 3 failed")
        raise

    finally:
        range_pulse_id = data_api_request["range"]
        start_pulse_id = range_pulse_id["startPulseId"]
        stop_pulse_id  = range_pulse_id["endPulseId"]

        rate_multiplicator = data_api_request.get("rate_multiplicator", 1)

        check_data_consistency(start_pulse_id, stop_pulse_id, rate_multiplicator, channels, output_file)


def check_data_consistency(start_pulse_id, stop_pulse_id, rate_multiplicator, channels, output_file):
    _logger.debug(f"data consistency check: {output_file}")

    start_time = time()

    expected_pulse_ids = np.arange(start_pulse_id, stop_pulse_id + 1)
    expected_pulse_ids = expected_pulse_ids[expected_pulse_ids % rate_multiplicator == 0]
    n_expected_pulse_id = len(expected_pulse_ids)

    #TODO: split function
    #TODO: close h5 file
    try:
        data_h5py = h5py.File(output_file)
        channels_in_file = set(data_h5py.keys())
        for channel in channels:
            if channel not in channels_in_file:
                _logger.error(f"check {channel} not present in file")
                continue

            raw_pulse_ids = data_h5py[f"/{channel}/pulse_id"][:]

            min_pulse_id_raw = min(raw_pulse_ids)
            if min_pulse_id_raw < start_pulse_id:
                _logger.error(f"check {channel} contains pulse IDs before the requested range: {min_pulse_id_raw} < {start_pulse_id}")

            max_pulse_id_raw = max(raw_pulse_ids)
            if max_pulse_id_raw > stop_pulse_id:
                _logger.error(f"check {channel} contains pulse IDs after the requested range: {max_pulse_id_raw} > {stop_pulse_id}")

            n_pulse_id_raw = len(raw_pulse_ids)
            n_unique_pulse_id_raw = len(set(raw_pulse_ids))

            duplicate_entries = (n_pulse_id_raw != n_unique_pulse_id_raw)

            if duplicate_entries:
                n_duplicate = n_pulse_id_raw - n_unique_pulse_id_raw
                _logger.error(f"check {channel} contains duplicate entries: total {n_pulse_id_raw}, duplicates {n_duplicate}")

            matched_pulse_id = np.intersect1d(expected_pulse_ids, raw_pulse_ids)
            n_matched_pulse_id = len(matched_pulse_id)

            if n_matched_pulse_id != n_expected_pulse_id:
                _logger.error(f"check {channel} number of (unique) pulse IDs {n_matched_pulse_id} differs from requested {n_expected_pulse_id}")

            start_matched_pulse_id = matched_pulse_id[0] if len(matched_pulse_id) else None
            start_expected = expected_pulse_ids[0]
            if start_matched_pulse_id != start_expected:
                _logger.error(f"check {channel} start pulse ID {start_matched_pulse_id} differs from requested {start_expected}")

            stop_matched_pulse_id = matched_pulse_id[-1] if len(matched_pulse_id) else None
            stop_expected = expected_pulse_ids[-1]
            if stop_matched_pulse_id != stop_expected:
                _logger.error(f"check {channel} stop pulse ID {stop_matched_pulse_id} differs from requested {stop_expected}")

            if start_matched_pulse_id == start_expected and stop_matched_pulse_id == stop_expected and not duplicate_entries:
                for pi, epi in zip(matched_pulse_id, expected_pulse_ids):
                    if pi != epi:
                        _logger.error(f"check {channel} pulse IDs are not monotonic: {pi} != {epi}")
                        break

    except Exception:
        _logger.exception("data consistency check failed")
        raise

    finally:
        time_delta = time() - start_time
        _logger.info(f"data consistency check took {time_delta} seconds")


def tsfmt(ts):
    ts = ts // 1000
    n = ts // 1000000
    m = ts % 1000000
    tz = pytz.timezone("UTC")
    fmt = "%Y-%m-%dT%H:%M:%S"
    s = datetime.fromtimestamp(n).astimezone(tz).strftime(fmt)
    return f"{s}.{m:06d}Z"



