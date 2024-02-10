import argparse
import logging
import socket

import bottle

from sf_daq_broker.broker_manager_slow import DetectorManager
from sf_daq_broker.rest_api import register_rest_api


_logger = logging.getLogger(__name__)


ENDPOINTS_POST = [
    "get_detector_settings",
    "set_detector_settings",
    "copy_user_files",
    "get_dap_settings",
    "set_dap_settings"
]



def start_server(rest_port):
    _logger.info("Starting Detector Settings Server")

    app = bottle.Bottle()
    manager = DetectorManager()

    register_rest_api(app, manager, endpoints_post=ENDPOINTS_POST)

    hostname = socket.gethostname()
    _logger.info(f"Starting Detector Settings Server REST-API on {hostname}:{rest_port}")

    bottle.run(app=app, host=hostname, port=rest_port)


def run():
    parser = argparse.ArgumentParser(description="detector settings")

    parser.add_argument("--rest_port", default=10003, type=int, help="REST-API port")
    parser.add_argument("--log_level", default="INFO", choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"], help="log level")

    clargs = parser.parse_args()

    logging.basicConfig(level=clargs.log_level, format="[%(levelname)s] %(message)s")

    start_server(clargs.rest_port)





if __name__ == "__main__":
    run()



