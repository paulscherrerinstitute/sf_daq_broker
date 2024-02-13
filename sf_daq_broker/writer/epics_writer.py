import logging
from math import isnan
from time import sleep, time

import numpy as np
import requests

from sf_daq_broker.config import DATA_API_QUERY_ADDRESS
from sf_daq_broker.utils import pulse_id_to_seconds
#TODO: the following does not exist!
from sf_daq_broker.writer.bsread_writer import BsreadH5Writer # pylint: disable=no-name-in-module


_logger = logging.getLogger("broker_writer")

N_RETRY_LIMIT = 5
N_RETRY_TIMEOUT = 10



def write_epics_pvs(output_file, start_pulse_id, stop_pulse_id, _metadata, epics_pvs): #TODO: what is _metadata for?
    _logger.info(f"writing output file {output_file} from start pulse ID {start_pulse_id} to stop pulse ID {stop_pulse_id}")
    _logger.debug(f"requesting PVs: {epics_pvs}")

    # download the data
    start_time = time()

    start_seconds = pulse_id_to_seconds(start_pulse_id)
    stop_seconds  = pulse_id_to_seconds(stop_pulse_id)

    data = get_data(epics_pvs, start_seconds, stop_seconds)

    delta_time = time() - start_time
    _logger.info(f"data download took {delta_time} seconds")

    if len(data) == 0:
        raise RuntimeError(f"no data received for requested PVs {epics_pvs}")

    # write the data to file
    start_time = time()

    with EpicsH5Writer(output_file) as writer:
        processed_data = writer.write_data(data, start_seconds)

    delta_time = time() - start_time
    _logger.info(f"data writing took {delta_time} seconds")

    verify_data(epics_pvs, processed_data)


def get_data(channel_list, start_seconds, stop_seconds):
    _logger.info(f"requesting timestamp range {start_seconds} to {stop_seconds} for channels: {channel_list}")

    #TODO: why remove PVs that hold units?
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

    _logger.debug(f"Data API query: {query}")

    for n_try in range(N_RETRY_LIMIT):
        response = requests.post(DATA_API_QUERY_ADDRESS, json=query)

        if response.status_code != 200:
            _logger.warning(f"data retrieval failed #{n_try+1}/{N_RETRY_LIMIT} -- will try again in {N_RETRY_TIMEOUT} seconds")
            sleep(N_RETRY_TIMEOUT)
            continue

        nbytes = len(response.content)
        _logger.info(f"downloaded {nbytes} bytes")
        return response.json()

    raise RuntimeError(f"failed {N_RETRY_LIMIT} times to retrieve data: {response}")


def verify_data(pv_list, processed_data):
    for pv in pv_list:
        if pv not in processed_data:
            _logger.error(f"PV {pv} not present")



class EpicsH5Writer(BsreadH5Writer):

    def write_data(self, json_data, start_seconds):
        data = self.group_data_by_channel(json_data)

        for channel_name, channel_data in data.items():
            dataset_type, _shape, timestamps, values = channel_data

            if dataset_type in ("string", "object"):
#                dataset_type = h5py.special_dtype(vlen=str)
                _logger.warning(f"cannot write string data of PV {channel_name}")
                continue

            timestamps = np.array(timestamps, dtype="int64")
            values = np.array(values, dtype=dataset_type)

            # nan values are marked as False, i.e., not changed
            change_in_interval = [False if isnan(x) else x > start_seconds for x in timestamps]

            #TODO: ugly, fix.
            if change_in_interval:
                if change_in_interval[0] is True:
                    _logger.error(f"PV {channel_name} does not have data point before start of acquisition")

                if any(x is False for x in change_in_interval[1:]):
                    _logger.error(f"PV {channel_name} has corrupted data")

            dataset_base = "/" + channel_name

            self.file.create_dataset(dataset_base + "/data",                data=values, dtype=dataset_type)
            self.file.create_dataset(dataset_base + "/timestamp",           data=timestamps)
            self.file.create_dataset(dataset_base + "/changed_in_interval", data=change_in_interval)

        return data


    def group_data_by_channel(self, raw_data):
        data = {}
        for channel_data in raw_data:
            channel_name = channel_data["channel"]["name"]

            timestamp_data = [int(float(x["globalSeconds"]) * 10**9) for x in channel_data["data"]]
            value_data = [x["value"] for x in channel_data["data"]]

#            type_data  = [x["type"]  for x in channel_data["data"]]
#            shape_data = [x["shape"] for x in channel_data["data"]]

            # use default values
            if not timestamp_data or not value_data:
                _logger.error(f"no data for PV {channel_name}")
                timestamp_data = []
                value_data = [float("nan")]
#                type_data = ["float64"]
#                shape_data = [[1]]

#            channel_type  = type_data[0]
#            channel_shape = shape_data[0]

#            if any(x != channel_type for x in type_data):
#                raise RuntimeError(f"data type for PV {channel_name} changed during scan")

#            if any(x != channel_shape for x in shape_data):
#                raise RuntimeError(f"data shape for PV {channel_name} changed during scan")

            response = requests.post("https://data-api.psi.ch/sf-archiverappliance/channels/config", json={"regex": channel_name})
            if response.status_code != 200:
                _logger.warning(f"config request for PV {channel_name} failed: {response}")
                continue

            response_data = response.json()
            #_logger.warning(f"PV {channel_name} config: {response_data}")

            found_channel_config = False

            channels = response_data[0]["channels"]

            if not channels:
                _logger.error(f"config for PV {channel_name} does not exist: received no channel data")
            else:
                for ch in channels:
                    if ch["name"] == channel_name:
                        found_channel_config = True
                        channel_type  = ch["type"]
                        channel_shape = ch["shape"]
                        break
                if not found_channel_config:
                    _logger.error(f"config for PV {channel_name} does not exist: PV not found in channel data")

            # use default values
            if not found_channel_config:
#                timestamp_data = []
#                value_data = [float("nan")]
                channel_type = "float64"
                channel_shape = [1]

            #_logger.warning(f"{channel_name} {channel_type} {channel_shape} {timestamp_data} {value_data}")
            data[channel_name] = (channel_type, channel_shape, timestamp_data, value_data)

        return data



