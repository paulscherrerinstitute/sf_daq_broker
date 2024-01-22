import argparse
import logging
import socket

import bottle

from sf_daq_broker.broker_manager_slow import DetectorManager
from sf_daq_broker.rest_api_slow import register_rest_interface

_logger = logging.getLogger(__name__)


def start_server(rest_port):

    _logger.info(f"Starting detector server on port {rest_port} (rest-api)")

    app = bottle.Bottle()

    manager = DetectorManager()

    logging.getLogger("pika").setLevel(logging.WARNING)

    register_rest_interface(app, manager)

    _logger.info("Detector Server started.")

    hostname = socket.gethostname()
    _logger.info(f"Starting rest API on port {rest_port} host {hostname}" )
    bottle.run(app=app, host=hostname, port=rest_port)


def run():
    parser = argparse.ArgumentParser(description="detector_settings")

    parser.add_argument("--rest_port", type=int, help="Port for REST api.", default=10003)

    parser.add_argument("--log_level", default="INFO",
                        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
                        help="Log level to use.")

    arguments = parser.parse_args()

    # Setup the logging level.
    logging.basicConfig(level=arguments.log_level, format="[%(levelname)s] %(message)s")

    start_server(rest_port=arguments.rest_port)


if __name__ == "__main__":
    run()
