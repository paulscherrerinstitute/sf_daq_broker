from datetime import datetime
import logging
from time import time, sleep

import dateutil.parser
import h5py
import pytz
import requests
import numpy

from sf_daq_broker.writer.bsread_writer import BsreadH5Writer

_logger = logging.getLogger("broker_writer")

DATA_API_QUERY_URL = "https://data-api.psi.ch/sf/query"
PULSE_ID_MAPPING_CHANNEL = "SIN-CVME-TIFGUN-EVR0:BUNCH-1-OK"
TIMEZONE = pytz.timezone('Europe/Zurich')
TARGET_MAPPING_DELAY_SECONDS = 30
N_RETRY_LIMIT = 5
N_RETRY_TIMEOUT = 10


def write_epics_pvs(output_file, start_pulse_id, stop_pulse_id, metadata, epics_pvs):
    _logger.info("Writing %s from start_pulse_id %s to stop_pulse_id %s."
                 % (output_file, start_pulse_id, stop_pulse_id))
    _logger.debug("Requesting PVs: %s" % epics_pvs)

    start_time = time()

    start_date = get_pulse_id_date_mapping(start_pulse_id)
    stop_date = get_pulse_id_date_mapping(stop_pulse_id)

    data = get_data(epics_pvs, start=start_date, stop=stop_date)

    _logger.info("Data download took %s seconds." % (time() - start_time))

    if len(data) == 0:
        raise RuntimeError("No data received for requested channels.")

    start_time = time()

    with EpicsH5Writer(output_file, metadata) as writer:
        writer.write_data(data, start_date)

    _logger.info("Data writing took %s seconds." % (time() - start_time))


def get_data(channel_list, start=None, stop=None):
    _logger.info("Requesting range %s to %s for channels: %s" %
                 (start, stop, channel_list))

    query = {"range": {"startDate": datetime.isoformat(start),
                       "endDate": datetime.isoformat(stop),
                       "startExpansion": True,
                       "endInclusive": True},
             "channels": channel_list,
             "fields": ["globalDate", "value", "type", "shape"]}

    _logger.debug("Data-api query: %s" % query)

    for i in range(N_RETRY_LIMIT):
        response = requests.post(DATA_API_QUERY_URL, json=query)

        # Check for successful return of data.
        if response.status_code != 200:
            _logger.warning("Data retrieval failed."
                            " Trying again after %s seconds." % N_RETRY_TIMEOUT)
            sleep(N_RETRY_TIMEOUT)
            continue

        _logger.info("Downloaded %d bytes." % len(response.content))
        return response.json()

    raise RuntimeError("Unable to retrieve data from server: ", response)


def get_pulse_id_date_mapping(pulse_id):
    _logger.info("Retrieve pulse-id/date mapping for pulse_id %s" % pulse_id)

    try:
        query = {"range": {"startPulseId": 0,
                           "endPulseId": pulse_id},
                 "limit": 1,
                 "ordering": "desc",
                 "channels": [PULSE_ID_MAPPING_CHANNEL],
                 "fields": ["pulseId", "globalDate"]}

        def retrieve_mapping():

            response = requests.post("https://data-api.psi.ch/sf/query", json=query)

            # Check for successful return of data
            if response.status_code != 200:
                raise RuntimeError("Unable to retrieve data from data-api: ", response)

            try:
                data = response.json()
                mapping_data = data[0]["data"][0]
                mapping_pulse_id = mapping_data["pulseId"]
                mapping_global_date = mapping_data["globalDate"]

            except Exception as ex:
                raise RuntimeError("Unexpected response from data-api: %s" % data) from ex

            return mapping_pulse_id, dateutil.parser.parse(mapping_global_date)

        received_pulse_id, global_date = retrieve_mapping()

        if received_pulse_id != pulse_id:
            _logger.warning("Requested pulse_id %s but received %s.")

            time_since_last_record = (datetime.now(TIMEZONE) - global_date).total_seconds()
            to_sleep = max(0., TARGET_MAPPING_DELAY_SECONDS - time_since_last_record)

            if to_sleep:
                _logger.info("Retrying in %s seconds." % to_sleep)
                sleep(to_sleep)

                received_pulse_id, global_date = retrieve_mapping()

            if received_pulse_id != pulse_id:
                raise RuntimeError('Cannot find requested pulse_id.')

        return global_date

    except Exception as e:
        raise RuntimeError('Cannot map pulse_id to global_date.') from e


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

    def write_data(self, json_data, start_date):
        data = self._group_data_by_channel(json_data)

        for channel_name, channel_data in data.items():
            dataset_type = channel_data[0]
            print(channel_name, channel_data[1])

            if dataset_type == "string" or dataset_type == "object":
                dataset_type = h5py.special_dtype(vlen=str)
                continue

            global_dates = numpy.array(channel_data[2], dtype=h5py.special_dtype(vlen=str))

            values = numpy.array(channel_data[3], dtype=dataset_type)

            # x == x is False for NaN values. Nan values are marked as not changed.
            change_in_interval = [dateutil.parser.parse(x) > start_date
                                  if x == x else False for x in global_dates]

            dataset_base = "/data/" + channel_name

            self.file.create_dataset(dataset_base + "/data",
                                     data=values,
                                     dtype=dataset_type)

            self.file.create_dataset(dataset_base + "/global_date",
                                     data=global_dates)

            self.file.create_dataset(dataset_base + "/changed_in_interval",
                                     data=change_in_interval)
