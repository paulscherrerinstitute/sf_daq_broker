import logging

_logger = logging.getLogger("broker_writer")

try:
    import ujson as json
except:
    _logger.warning("There is no ujson in this environment. Performance will suffer.")
    import json


def write_from_detectorbuffer(data_api_request, output_file, metadata):
    _logger.debug("Data API request: %s", data_api_request)
