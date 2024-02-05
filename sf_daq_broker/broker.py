import argparse
import logging
import socket

import bottle

import sf_daq_broker.rabbitmq.config as broker_config
from sf_daq_broker import config
from sf_daq_broker.broker_manager import BrokerManager
from sf_daq_broker.rabbitmq.msg_broker_client import RabbitMqClient
from sf_daq_broker.rest_api import register_rest_api


_logger = logging.getLogger(__name__)


ENDPOINTS_POST = [
    "retrieve_from_buffers",
    "take_pedestal",
    "power_on_detector",
    "set_pvlist",
    "close_pgroup_writing"
]

ENDPOINTS_GET = [
    "get_allowed_detectors_list",
    "get_running_detectors_list",
    "get_next_run_number",
    "get_last_run_number",
    "get_pvlist"
]



def start_server(broker_url, rest_port):
    _logger.info(f"Starting sf_daq_broker message broker on {broker_url}")

    broker_client = RabbitMqClient(broker_url=broker_url)
    logging.getLogger("pika").setLevel(logging.WARNING)

    _logger.info("sf_daq_broker message broker started")

    app = bottle.Bottle()
    manager = BrokerManager(broker_client=broker_client)

    register_rest_api(app, manager, endpoints_post=ENDPOINTS_POST, endpoints_get=ENDPOINTS_GET)

    hostname = socket.gethostname()
    _logger.info(f"Starting sf_daq_broker REST-API on {hostname}:{rest_port}")

    bottle.run(app=app, host=hostname, port=rest_port)


def run():
    parser = argparse.ArgumentParser(description="sf_daq_broker")

    parser.add_argument("--broker_url", default=broker_config.DEFAULT_BROKER_URL, help="Message broker URL")
    parser.add_argument("--rest_port", default=config.DEFAULT_BROKER_REST_PORT, type=int, help="REST-API port")
    parser.add_argument("--log_level", default=config.DEFAULT_LOG_LEVEL, choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"], help="Log level")

    clargs = parser.parse_args()

    logging.basicConfig(level=clargs.log_level, format="[%(levelname)s] %(message)s")

    start_server(clargs.broker_url, clargs.rest_port)





if __name__ == "__main__":
    run()



