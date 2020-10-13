from datetime import datetime
import time
import logging

import dateutil
import pytz
import requests


import pandas

_logger = logging.getLogger("broker_writer")

DATA_API_QUERY_URL = "https://data-api.psi.ch/sf/query"
PULSE_ID_MAPPING_CHANNEL = "SIN-CVME-TIFGUN-EVR0:BUNCH-1-OK"
TIMEZONE = pytz.timezone('Europe/Zurich')
TARGET_MAPPING_DELAY_SECONDS = 30
N_RETRY_LIMIT = 5
N_RETRY_TIMEOUT = 10


def write_epics_pvs(output_file, start_pulse_id, stop_pulse_id, metadata, epics_pvs):
    import data_api

    start_date = get_pulse_id_date_mapping(start_pulse_id)
    stop_date = get_pulse_id_date_mapping(stop_pulse_id)

    mapping_data = get_data([PULSE_ID_MAPPING_CHANNEL], start=start_date, stop=stop_date)
    data = get_data(epics_pvs, start=start_date, stop=stop_date)

    aligned_data = map_data_to_pulse_id(data, mapping_data)


    # TODO: Merge metadata to data.

    if len(data) > 0:
        _logger.info("Persist data to hdf5 file")
        data_api.to_hdf5(data, output_file, overwrite=True, compression=None, shuffle=False)
    else:
        _logger.error("No data retrieved")
        open(output_file + "_NO_DATA", 'a').close()


def map_data_to_pulse_id(data, mapping_data):
    # There is always only 1 channel for mapping.
    mapping_data = mapping_data[0]["data"]
    # The last 6 digits of the globalSeconds == last 6 digits of pulse_id. Discard.
    mapping_generator = ((float(x["globalSeconds"][:-6]), x["pulseId"])
                         for x in mapping_data)
    mapping_df = pandas.DataFrame(mapping_generator, columns=["globalSeconds", "pulse_id"])
    mapping_df = mapping_df.set_index("globalSeconds").sort_index()


    for channel in server_data:
        channel_name = channel["channel"]["name"]
        channel_data = channel["data"]

        # Channel_data is a list of values.
        is_data_present = bool(channel_data)
    return None


def get_data(channel_list, start=None, stop=None):
    _logger.info("Requesting range %s to %s for channels: %s" %
                 (start, stop, channel_list))

    query = {"range": {"startDate": datetime.isoformat(start),
                       "endDate": datetime.isoformat(stop),
                       "startExpansion": True,
                       "endInclusive": True},
             "channels": channel_list,
             "fields": ["pulseId", "globalSeconds", "globalDate", "value",
                        "eventCount"]}

    _logger.debug("Data-api query: %s" % query)

    for i in range(N_RETRY_LIMIT):
        response = requests.post(DATA_API_QUERY_URL, json=query)

        # Check for successful return of data.
        if response.status_code != 200:
            _logger.warning("Data retrieval failed."
                            " Trying again after %s seconds." % N_RETRY_TIMEOUT)
            time.sleep(N_RETRY_TIMEOUT)
            continue

        return response.json()

    raise RuntimeError("Unable to retrieve data from server: ", response)


def get_pulse_id_date_mapping(pulse_id):
    # See https://jira.psi.ch/browse/ATEST-897 for more details ...
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
                time.sleep(to_sleep)

                received_pulse_id, global_date = retrieve_mapping()

            if received_pulse_id != pulse_id:
                raise RuntimeError('Cannot find requested pulse_id.')

        return global_date

    except Exception as e:
        raise RuntimeError('Cannot map pulse_id to global_date.') from e
