import logging
from time import time, sleep

import dateutil.parser
import h5py
import requests
import numpy

from sf_daq_broker.config import DATA_API_QUERY_ADDRESS
from sf_daq_broker.utils import pulse_id_to_seconds
from sf_daq_broker.writer.bsread_writer import BsreadH5Writer

_logger = logging.getLogger("broker_writer")

N_RETRY_LIMIT = 5
N_RETRY_TIMEOUT = 10


def write_epics_pvs(output_file, start_pulse_id, stop_pulse_id, metadata, epics_pvs):
    _logger.info("Writing %s from start_pulse_id %s to stop_pulse_id %s."
                 % (output_file, start_pulse_id, stop_pulse_id))
    _logger.debug("Requesting PVs: %s" % epics_pvs)

    start_time = time()

    start_seconds = pulse_id_to_seconds(start_pulse_id)
    stop_seconds = pulse_id_to_seconds(stop_pulse_id)

    data = get_data(epics_pvs, start_seconds=start_seconds, stop_seconds=stop_seconds)

    _logger.info("Data download took %s seconds." % (time() - start_time))

    if len(data) == 0:
        raise RuntimeError("No data received for requested channels.")

    start_time = time()

    with EpicsH5Writer(output_file) as writer:
        writer.write_data(data, start_seconds)

    _logger.info("Data writing took %s seconds." % (time() - start_time))


def get_data(channel_list, start_seconds=None, stop_seconds=None):
    _logger.info("Requesting range %s to %s for channels: %s" %
                 (start_seconds, stop_seconds, channel_list))

    query = {"range": {"startSeconds": start_seconds,
                       "endSeconds": stop_seconds,
                       "startExpansion": True,
                       "endInclusive": True},
             "channels": channel_list,
             "fields": ["globalDate", "value", "type", "shape"]}

    _logger.debug("Data-api query: %s" % query)

    for i in range(N_RETRY_LIMIT):
        response = requests.post(DATA_API_QUERY_ADDRESS, json=query)

        # Check for successful return of data.
        if response.status_code != 200:
            _logger.warning("Data retrieval failed."
                            " Trying again after %s seconds." % N_RETRY_TIMEOUT)
            sleep(N_RETRY_TIMEOUT)
            continue

        _logger.info("Downloaded %d bytes." % len(response.content))
        return response.json()

    raise RuntimeError("Unable to retrieve data from server: ", response)


class EpicsH5Writer(BsreadH5Writer):

    def _group_data_by_channel(self, raw_data):
        data = {}
        for channel_data in raw_data:
            channel_name = channel_data["channel"]["name"]

            global_date_data = [x["globalDate"] for x in channel_data["data"]]
            value_data = [x["value"] for x in channel_data["data"]]
            type_data = [x["type"] for x in channel_data["data"]]
            shape_data = [x["shape"] for x in channel_data["data"]]

            if len(global_date_data) == 0 or len(value_data) == 0:
                global_date_data = []
                value_data = [float("nan")]
                type_data = ["float64"]
                shape_data = [[1]]

            channel_type = type_data[0]
            channel_shape = shape_data[0]

            if any((x != channel_type for x in type_data)):
                raise RuntimeError("Channel %s data type changed during scan." % channel_name)

            if any((x != channel_shape for x in shape_data)):
                raise RuntimeError("Channel %s data shape changed during scan" % channel_name)

            data[channel_name] = [channel_type, channel_shape, global_date_data, value_data]

        return data

    def write_data(self, json_data, start_seconds):
        data = self._group_data_by_channel(json_data)

        for channel_name, channel_data in data.items():
            dataset_type = channel_data[0]
            print(channel_name, channel_data[1])

            if dataset_type == "string" or dataset_type == "object":
                dataset_type = h5py.special_dtype(vlen=str)
                _logger.warning("Writing of string data not supported. Channel %s omitted." % channel_name)
                continue

            global_dates = numpy.array(channel_data[2], dtype=h5py.special_dtype(vlen=str))

            values = numpy.array(channel_data[3], dtype=dataset_type)

            # x == x is False for NaN values. Nan values are marked as not changed.
            change_in_interval = [dateutil.parser.parse(x).timestamp() > start_seconds
                                  if x == x else False for x in global_dates]

            dataset_base = "/data/" + channel_name

            self.file.create_dataset(dataset_base + "/data",
                                     data=values,
                                     dtype=dataset_type)

            self.file.create_dataset(dataset_base + "/global_date",
                                     data=global_dates)

            self.file.create_dataset(dataset_base + "/changed_in_interval",
                                     data=change_in_interval)
