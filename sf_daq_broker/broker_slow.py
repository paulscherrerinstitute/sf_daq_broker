import argparse
import logging
import socket

import bottle

from sf_daq_broker import config
from sf_daq_broker.broker_manager_slow import DetectorManager
from sf_daq_broker.rest_api import register_rest_api


_logger = logging.getLogger(__name__)


ENDPOINTS_POST = [
    "set_detector_settings",
    "copy_user_files",
    "set_dap_settings"
]

ENDPOINTS_GET = [
    "get_dap_settings",
    "get_detector_settings",
    "get_jfctrl_monitor",
    "get_detector_temperatures"
]



def run():
    parser = argparse.ArgumentParser(description="detector settings server")

    parser.add_argument("--rest_port", default=config.DEFAULT_BROKER_SLOW_REST_PORT, type=int, help="REST-API port")
    parser.add_argument("--log_level", default=config.DEFAULT_LOG_LEVEL, choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"], help="log level")

    clargs = parser.parse_args()

    logging.basicConfig(level=clargs.log_level, format=config.LOG_FORMAT)

    start_server(clargs.rest_port)


def start_server(rest_port):
    _logger.info("starting detector settings server")

    app = bottle.Bottle()
    manager = DetectorManager()

    register_rest_api(app, manager, endpoints_post=ENDPOINTS_POST, endpoints_get=ENDPOINTS_GET)

    hostname = socket.gethostname()
    _logger.info(f"starting detector settings server REST-API on {hostname}:{rest_port}")

    bottle.run(app=app, host=hostname, port=rest_port)





if __name__ == "__main__":
    run()



