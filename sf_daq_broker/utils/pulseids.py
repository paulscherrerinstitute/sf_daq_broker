import logging
from time import sleep

import requests

from sf_daq_broker import config


_logger = logging.getLogger("broker_writer")



def pulse_id_to_seconds(pulse_id, **kwargs):
    ts = pulse_id_to_timestamp(pulse_id, **kwargs)
    return ts / 1e9


def pulse_id_to_timestamp(pulse_id, n_tries=3, wait_time=5):
    url = f"{config.PULSEID2SECONDS_MATCHING_ADDRESS}/{pulse_id}"

    for i in range(n_tries):
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()

        _logger.warning(f"mapping pulse ID {pulse_id} to timestamp failed #{i+1}/{n_tries} -- will try again in {wait_time} seconds")
        sleep(wait_time)

    msg = f"mapping pulse ID {pulse_id} to timestamp failed {n_tries} times: {response}"
    _logger.error(msg)
    raise RuntimeError(msg)



