import logging
import os
from datetime import datetime
from time import time
import pytz

import h5py
import numpy
import requests
from random import randrange
from copy import deepcopy

from sf_daq_broker import config, utils
from sf_daq_broker.writer.utils import channel_type_deserializer_mapping

_logger = logging.getLogger("broker_writer")

try:
    import ujson as json
except:
    _logger.warning("There is no ujson in this environment. Performance will suffer.")
    import json

def tsfmt(ts):
    ts = ts // 1000
    n = ts // 1000000
    m = ts % 1000000
    s = datetime.fromtimestamp(n).astimezone(pytz.timezone('UTC')).strftime("%Y-%m-%dT%H:%M:%S")
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
                _logger.error(f'check {channel} not present in file')
            else:

                pulse_id_raw    = data_h5py[f'/{channel}/pulse_id'][:]

                if numpy.sum(pulse_id_raw < start_pulse_id) or numpy.sum(pulse_id_raw > stop_pulse_id):
                    _logger.error(f'check {channel} contains pulse_id outside of requested range')

                n_pulse_id_raw = len(pulse_id_raw)

                n_unique_pulse_id_raw = len(set(pulse_id_raw))

                duplicated_entries = False
                if n_pulse_id_raw != n_unique_pulse_id_raw:
                    duplicated_entries = True
                    _logger.error(f'check {channel} contains duplicated entries. Total entries : {n_pulse_id_raw}, duplicated entries : {n_pulse_id_raw-n_unique_pulse_id_raw} ')

                pulse_id = numpy.intersect1d(expected_pulse_id, pulse_id_raw)
                n_pulse_id = len(pulse_id)

                if n_pulse_id != expected_number_measurements:
                    _logger.error(f'check {channel} number of pulse_id(unique) is different from expected : {n_pulse_id} vs {expected_number_measurements}')
                else:
                    if pulse_id[0] != expected_pulse_id[0] or pulse_id[-1] != expected_pulse_id[-1]:
                        _logger.error(f'check {channel} start/stop pulse_id are not the one which are requested (requested : {expected_pulse_id[0]},{expected_pulse_id[-1]}, got: {pulse_id[0]},{pulse_id[-1]}) ')
                        if not duplicated_entries:
                            pulse_id_check = True
                            for i in range(n_pulse_id):
                                if pulse_id[i] != expected_pulse_id[i]:
                                    pulse_id_check = False
                            if not pulse_id_check:
                                _logger.error(f'check {channel} pulse_id are not monotonic')

    except Exception as e:
        _logger.error(f'check failed')
        _logger.error(e)

    _logger.info("Check of data consistency took %s seconds." % (time() - start_check_time))


def write_from_databuffer(data_api_request, output_file, metadata):

    _logger.debug("Data API request: %s", data_api_request)

    if config.TRANSFORM_PULSE_ID_TO_TIMESTAMP_QUERY:
        data_api_request = utils.transform_range_from_pulse_id_to_timestamp(data_api_request)

    start_time = time()

    new_data_api_request = deepcopy(data_api_request)

    response = requests.post(url=config.DATA_API_QUERY_ADDRESS, json=new_data_api_request, timeout=1000)
    data = json.loads(response.content)
    if not data:
        raise ValueError("Received data from data_api is empty.")

    # The response is a list if status is OK, otherwise its a dictionary, of course.
    if isinstance(data, dict):
        if data.get("status") == 500:
            raise Exception("Server returned error: %s" % data)

        raise Exception("Server returned a dict (keys: %s), but a list was expected." % list(data.keys()))

    _logger.info("Data download (%d bytes) took %s seconds." % (len(response.content), time() - start_time))

    start_time = time()

    with BsreadH5Writer(output_file) as writer:
        writer.write_data(data)

    _logger.info("Data writing took %s seconds." % (time() - start_time))


def write_from_imagebuffer(data_api_request, output_file, parameters):
    import data_api3.h5 as h5

    start_pulse_id = data_api_request["range"]["startPulseId"]
    stop_pulse_id  = data_api_request["range"]["endPulseId"]
    rate_multiplicator = data_api_request.get("rate_multiplicator", 1)

    _logger.debug("Data API request: %s", data_api_request)

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

    _logger.debug("Requesting '%s' to output_file %s from %s " %
                  (query, output_file, image_buffer_url))

    start_time = time()
  
    try:
        h5.request(query, output_file, url=image_buffer_url)
        _logger.info("Image download and writing took %s seconds." % (time() - start_time))
    except Exception as e:
        _logger.error("Got exception from data_api3")
        _logger.error(e)
        
    check_data_consistency(start_pulse_id, stop_pulse_id, rate_multiplicator, channels, output_file)

def write_from_databuffer_api3(data_api_request, output_file, parameters):
    import data_api3.h5 as h5

    _logger.debug("Data3 API request: %s", data_api_request)

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

    _logger.debug("Requesting '%s' to output_file %s from %s " %
                  (query, output_file, data_buffer_url))

    start_time = time()

    try:
        h5.request(query, filename=output_file, baseurl=data_buffer_url, default_backend=config.DATA_BACKEND)
        _logger.info("Data download and writing took %s seconds." % (time() - start_time))
    except Exception as e:
        _logger.error("Got exception from data_api3")
        _logger.error(e)


    check_data_consistency(start_pulse_id, stop_pulse_id, rate_multiplicator, channels, output_file)


class BsreadH5Writer(object):

    def __init__(self, output_file):

        self.output_file = output_file

        path_to_file = os.path.dirname(self.output_file)
        os.makedirs(path_to_file, exist_ok=True)

        self.file = h5py.File(self.output_file, "w")
        _logger.info("File %s created." % self.output_file)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _build_datasets_data(self, json_data):

        _logger.debug("Building numpy arrays with received data.")

        datasets_data = {}

        if not isinstance(json_data, list):
            raise ValueError("json_data should be a list, but its %s." % type(json_data))

        for channel_data in json_data:

            if not isinstance(channel_data, dict):
                raise ValueError("channel_data should be a dict, but its %s." % type(channel_data))

            try:
                name = channel_data["channel"]["name"]
                _logger.debug("Formatting data for channel %s." % name)

                data = channel_data["data"]
                if not data:
                    if config.ERROR_IF_NO_DATA:
                        raise ValueError("There is no data for channel %s." % name)
                    else:
                        _logger.error("There is no data for channel %s." % name)

                channel_type = channel_data["configs"][0]["type"]
                channel_shape = channel_data["configs"][0]["shape"]

                n_data_points = len(data)
                dataset_type, dataset_shape = self._get_dataset_definition(channel_type, channel_shape, n_data_points)

                dataset_values = numpy.zeros(dtype=dataset_type, shape=dataset_shape)
                dataset_value_present = numpy.zeros(shape=(n_data_points,), dtype="bool")
                dataset_pulse_ids = numpy.zeros(shape=(n_data_points,), dtype="<i8")
                dataset_global_time = numpy.zeros(shape=(n_data_points,), dtype=h5py.special_dtype(vlen=str))

                if data:
                    for data_index, data_point in enumerate(data):

                        if len(channel_shape) > 1:
                            # Bsread is [X, Y] but numpy is [Y, X].
                            data_point["value"] = numpy.array(data_point["value"], dtype=dataset_type). \
                                reshape(channel_shape[::-1])

                        dataset_values[data_index] = data_point["value"]
                        dataset_value_present[data_index] = 1
                        dataset_pulse_ids[data_index] = data_point["pulseId"]
                        dataset_global_time[data_index] = data_point["globalDate"]

                datasets_data[name] = {
                    "data": dataset_values,
                    "is_data_present": dataset_value_present,
                    "pulse_id": dataset_pulse_ids,
                    "global_date": dataset_global_time
                }

            except Exception as e:
                _logger.error("Cannot convert channel_name %s." % name)

                if config.ERROR_IF_NO_DATA:
                    raise

        return datasets_data

    def _get_dataset_definition(self, channel_dtype, channel_shape, n_data_points):

        dataset_type = channel_type_deserializer_mapping[channel_dtype][0]
        dataset_shape = [n_data_points] + channel_shape[::-1]

        if channel_dtype == "string":
            dataset_type = h5py.special_dtype(vlen=str)
            dataset_shape = [n_data_points] + channel_shape[::-1]

        return dataset_type, dataset_shape

    def write_data(self, json_data):

        _logger.info("Writing data to disk.")

        datasets_data = self._build_datasets_data(json_data)

        for name, data in datasets_data.items():
            self.file[name + "/pulse_id"] = data["pulse_id"]
            self.file[name + "/global_date"] = data["global_date"]
            self.file[name + "/data"] = data["data"]
            self.file[name + "/is_data_present"] = data["is_data_present"]

    def close(self):
        self.file.close()
