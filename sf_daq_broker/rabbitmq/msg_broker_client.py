import json

import sf_daq_broker.rabbitmq.config as broker_config

from pika import BlockingConnection, ConnectionParameters, BasicProperties


class RabbitMqClient(object):

    def __init__(self, broker_url=broker_config.DEFAULT_BROKER_URL):
        self.connection = BlockingConnection(ConnectionParameters(broker_url))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange=broker_config.REQUEST_EXCHANGE,
                                      exchange_type="topic")

        self.channel.exchange_declare(exchange=broker_config.STATUS_EXCHANGE,
                                      exchange_type="fanout")

    def close(self):
        self.connection.close()

    def send(self, tag, write_request):

        routing_key = "." + tag + "."

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
                                   routing_key="",
                                   body=body_bytes)
