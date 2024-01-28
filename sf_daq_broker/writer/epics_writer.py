import logging
from math import isnan
from time import sleep, time

import h5py
import numpy
import requests

from sf_daq_broker.config import DATA_API_QUERY_ADDRESS
from sf_daq_broker.utils import pulse_id_to_seconds
from sf_daq_broker.writer.bsread_writer import BsreadH5Writer #TODO: this does not exist!


_logger = logging.getLogger("broker_writer")

N_RETRY_LIMIT = 5
N_RETRY_TIMEOUT = 10



def verify_data(pv_list, processed_data):
    for pv in pv_list:
        if pv not in processed_data:
            _logger.error(f"PV {pv} not present.")


def write_epics_pvs(output_file, start_pulse_id, stop_pulse_id, _metadata, epics_pvs): #TODO: what is _metadata for?
    _logger.info(f"Writing {output_file} from start_pulse_id {start_pulse_id} to stop_pulse_id {stop_pulse_id}.")
    _logger.debug(f"Requesting PVs: {epics_pvs}")

    start_time = time()

    start_seconds = pulse_id_to_seconds(start_pulse_id)
    stop_seconds  = pulse_id_to_seconds(stop_pulse_id)

    data = get_data(epics_pvs, start_seconds=start_seconds, stop_seconds=stop_seconds)

    delta_time = time() - start_time
    _logger.info(f"Data download took {delta_time} seconds.")

    if len(data) == 0:
        raise RuntimeError("No data received for requested channels.")

    start_time = time()

    with EpicsH5Writer(output_file) as writer:
        processed_data = writer.write_data(data, start_seconds)

    delta_time = time() - start_time
    _logger.info(f"Data writing took {delta_time} seconds.")

    verify_data(epics_pvs, processed_data)


def get_data(channel_list, start_seconds=None, stop_seconds=None):
    _logger.info(f"Requesting range {start_seconds} to {stop_seconds} for channels: {channel_list}")

    clean_channel_list = [c for c in channel_list if ".EGU" not in c]

    query = {
        "range": {
            "startSeconds": start_seconds,
            "endSeconds": stop_seconds,
            "startExpansion": True,
            "endInclusive": True
        },
        "channels": clean_channel_list,
        "fields": ["globalSeconds", "value", "type", "shape"]
    }

    _logger.debug(f"Data-api query: {query}")

    for _ in range(N_RETRY_LIMIT):
        response = requests.post(DATA_API_QUERY_ADDRESS, json=query)

        # Check for successful return of data.
        if response.status_code != 200:
            _logger.warning(f"Data retrieval failed. Trying again after {N_RETRY_TIMEOUT} seconds.")
            sleep(N_RETRY_TIMEOUT)
            continue

        nbytes = len(response.content)
        _logger.info(f"Downloaded {nbytes} bytes.")
        return response.json()

    raise RuntimeError("Unable to retrieve data from server: ", response)



class EpicsH5Writer(BsreadH5Writer):

    def _group_data_by_channel(self, raw_data):
        data = {}
        for channel_data in raw_data:
            channel_name = channel_data["channel"]["name"]

            timestamp_data = [int(float(x["globalSeconds"]) * 10**9) for x in channel_data["data"]]
            value_data = [x["value"] for x in channel_data["data"]]

#            type_data  = [x["type"]  for x in channel_data["data"]]
#            shape_data = [x["shape"] for x in channel_data["data"]]

            if len(timestamp_data) == 0 or len(value_data) == 0:
                _logger.error(f"Data for PV {channel_name} does not exist.")
                timestamp_data = []
                value_data = [float("nan")]
#                type_data = ["float64"]
#                shape_data = [[1]]

#            channel_type  = type_data[0]
#            channel_shape = shape_data[0]

#            if any(x != channel_type for x in type_data):
#                raise RuntimeError(f"Channel {channel_name} data type changed during scan.")

#            if any(x != channel_shape for x in shape_data):
#                raise RuntimeError(f"Channel {channel_name} data shape changed during scan")

            response = requests.post("https://data-api.psi.ch/sf-archiverappliance/channels/config", json={"regex": channel_name})
            if response.status_code != 200:
                _logger.warning(f"Channel {channel_name} request config failed. {response}")
                continue

            response_data = response.json()
            #_logger.warning(f"Channel {channel_name} config : {response_data}")

            channels = response_data[0]["channels"]
            if len(channels) == 0:
                _logger.error(f"Config for PV {channel_name} does not exist. Reason 1")
                timestamp_data = []
                value_data = [float("nan")]
                channel_type = "float64"
                channel_shape = [1]
            else:
                found_channel_config = False
                for ch in channels:
                    if ch["name"] == channel_name:
                        found_channel_config = True
                        channel_type  = ch["type"]
                        channel_shape = ch["shape"]

                if not found_channel_config:
                    _logger.error(f"Config for PV {channel_name} does not exist. Reason 2")
                    timestamp_data = []
                    value_data = [float("nan")]
                    channel_type = "float64"
                    channel_shape = [1]

            #_logger.warning(f"{channel_name} {channel_type} {channel_shape} {timestamp_data} {value_data}")
            data[channel_name] = [channel_type, channel_shape, timestamp_data, value_data]

        return data


    def write_data(self, json_data, start_seconds):
        data = self._group_data_by_channel(json_data)

        for channel_name, channel_data in data.items():
            dataset_type = channel_data[0]

            if dataset_type in ("string", "object"):
                dataset_type = h5py.special_dtype(vlen=str)
                _logger.warning(f"Writing of string data not supported. Channel {channel_name} omitted.")
                continue

            timestamps = numpy.array(channel_data[2], dtype="int64")
            values = numpy.array(channel_data[3], dtype=dataset_type)

            # Nan values are marked as False, i.e., not changed.
            change_in_interval = [False if isnan(x) else x > start_seconds for x in timestamps]

            #TODO: Ugly, fix.
            if change_in_interval:
                if change_in_interval[0] is True:
                    _logger.error(f"PV {channel_name} does not have a data point before start of acquisition.")

                if any(x is False for x in change_in_interval[1:]):
                    _logger.error(f"PV {channel_name} has corrupted data.")

            dataset_base = "/" + channel_name

            self.file.create_dataset(dataset_base + "/data",                data=values, dtype=dataset_type)
            self.file.create_dataset(dataset_base + "/timestamp",           data=timestamps)
            self.file.create_dataset(dataset_base + "/changed_in_interval", data=change_in_interval)

        return data



