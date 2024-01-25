import argparse
import logging

import bottle
import socket

from sf_daq_broker import config
import sf_daq_broker.rabbitmq.config as broker_config
from sf_daq_broker.broker_manager import BrokerManager
from sf_daq_broker.rabbitmq.msg_broker_client import RabbitMqClient
from sf_daq_broker.rest_api import register_rest_interface

_logger = logging.getLogger(__name__)


def start_server(broker_url, rest_port):

    _logger.info("Starting sf_daq_broker on port %s (rest-api) with broker_url(message-broker) %s" % (rest_port, broker_url))

    app = bottle.Bottle()

    broker_client = RabbitMqClient(broker_url=broker_url)
    manager = BrokerManager(broker_client=broker_client)

    logging.getLogger("pika").setLevel(logging.WARNING)

    register_rest_interface(app, manager)

    _logger.info("SF-DAQ-BROKER started.")

    # TODO: this is broken because `hostname` can be completely different from the given broker-url. 
    try:
        hostname = socket.gethostname()
        _logger.info("Starting rest API on port %s host %s" % (rest_port, hostname) )
        bottle.run(app=app, host=hostname, port=rest_port)
    finally:
        pass


def run():
    parser = argparse.ArgumentParser(description='sf_daq_broker')

    parser.add_argument("--broker_url", default=broker_config.DEFAULT_BROKER_URL,
                        help="Address of the message broker")

    parser.add_argument("--rest_port", type=int, help="Port for REST api.", default=config.DEFAULT_BROKER_REST_PORT)

    parser.add_argument("--log_level", default=config.DEFAULT_LOG_LEVEL,
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")

    arguments = parser.parse_args()

    # Setup the logging level.
    logging.basicConfig(level=arguments.log_level, format='[%(levelname)s] %(message)s')

    start_server(broker_url=arguments.broker_url,
                 rest_port=arguments.rest_port)


if __name__ == "__main__":
    run()
