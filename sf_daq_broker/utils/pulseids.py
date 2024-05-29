import logging
from time import sleep

import requests

from sf_daq_broker import config
from .excfmt import dueto


_logger = logging.getLogger("broker_writer")



#def pulse_id_to_seconds(pulse_id, **kwargs):
#    ts = pulse_id_to_timestamp(pulse_id, **kwargs)
#    return ts / 1e9


def pulse_id_to_timestamp(pulse_id, n_tries=15, wait_time=5):
    url = f"{config.PULSEID2SECONDS_MATCHING_ADDRESS}/{pulse_id}"

    for i in range(n_tries):
        count = i + 1
        try:
            return request_get(url)
        except Exception as e:
            _logger.warning(f"mapping pulse ID {pulse_id} to timestamp failed #{count}/{n_tries} {dueto(e)} -- will try again in {wait_time * count} seconds")
            sleep(wait_time * count)

    msg = f"mapping pulse ID {pulse_id} to timestamp failed {n_tries} times"
    _logger.error(msg)
    raise RuntimeError(msg)


def request_get(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()



