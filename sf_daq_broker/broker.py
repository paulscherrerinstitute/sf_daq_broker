import argparse
import logging
import socket

import bottle

import sf_daq_broker.rabbitmq.config as broker_config
from sf_daq_broker import config
from sf_daq_broker.broker_manager import BrokerManager
from sf_daq_broker.rabbitmq.msg_broker_client import RabbitMqClient
from sf_daq_broker.rest_api import register_rest_interface


_logger = logging.getLogger(__name__)



def start_server(broker_url, rest_port):
    _logger.info(f"Starting sf_daq_broker on port {rest_port} (rest-api) with broker_url(message-broker) {broker_url}")

    app = bottle.Bottle()
    broker_client = RabbitMqClient(broker_url=broker_url)
    manager = BrokerManager(broker_client=broker_client)

    logging.getLogger("pika").setLevel(logging.WARNING)

    register_rest_interface(app, manager)

    _logger.info("SF-DAQ-BROKER started.")

    hostname = socket.gethostname()
    _logger.info(f"Starting rest API on port {rest_port} host {hostname}" )

    bottle.run(app=app, host=hostname, port=rest_port)


def run():
    parser = argparse.ArgumentParser(description="sf_daq_broker")

    parser.add_argument("--broker_url", default=broker_config.DEFAULT_BROKER_URL, help="Address of the message broker")
    parser.add_argument("--rest_port", default=config.DEFAULT_BROKER_REST_PORT, type=int, help="Port for REST api.")
    parser.add_argument("--log_level", default=config.DEFAULT_LOG_LEVEL, choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"], help="Log level to use.")

    clargs = parser.parse_args()

    logging.basicConfig(level=clargs.log_level, format="[%(levelname)s] %(message)s")

    start_server(broker_url=clargs.broker_url, rest_port=clargs.rest_port)





if __name__ == "__main__":
    run()



