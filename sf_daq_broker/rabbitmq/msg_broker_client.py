import json

import sf_daq_broker.rabbitmq.config as broker_config

from pika import BlockingConnection, ConnectionParameters, BasicProperties

from time import sleep

class RabbitMqClient(object):

    def __init__(self, broker_url=broker_config.DEFAULT_BROKER_URL):
        self.broker_url = broker_url

        self.connection = None
        self.channel = None

    def open(self):
        try:
            self.connection = BlockingConnection(ConnectionParameters(self.broker_url))
        except:
            sleep(1)
            self.connection = BlockingConnection(ConnectionParameters(self.broker_url))

        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange=broker_config.REQUEST_EXCHANGE,
                                      exchange_type="topic")

        self.channel.exchange_declare(exchange=broker_config.STATUS_EXCHANGE,
                                      exchange_type="fanout")

    def close(self):
        self.connection.close()

        self.connection = None
        self.channel = None

    def send(self, write_request):

        if self.channel is None:
            raise RuntimeError("RabbitMqClient not connected.")

        routing_key = "*"

        body_bytes = json.dumps(write_request).encode()

        self.channel.basic_publish(exchange=broker_config.REQUEST_EXCHANGE,
                                   routing_key=routing_key,
                                   body=body_bytes)

        status_header = {
            "action": "write_request",
            "source": "BrokerClient",
            "routing_key": routing_key
        }

        self.channel.basic_publish(exchange=broker_config.STATUS_EXCHANGE,
                                   properties=BasicProperties(
                                       headers=status_header),
                                   routing_key=routing_key,
                                   body=body_bytes)
