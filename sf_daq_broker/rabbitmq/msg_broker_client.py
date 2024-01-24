import json
import uuid
from time import sleep

from pika import BasicProperties, BlockingConnection, ConnectionParameters

import sf_daq_broker.rabbitmq.config as broker_config


ROUTES = {
#    broker_config.TAG_DATA3BUFFER:       broker_config.DEFAULT_ROUTE,
#    broker_config.TAG_IMAGEBUFFER:       broker_config.DEFAULT_ROUTE,
    broker_config.TAG_DETECTOR_RETRIEVE: broker_config.DETECTOR_RETRIEVE_ROUTE,
    broker_config.TAG_DETECTOR_CONVERT:  broker_config.DETECTOR_CONVERSION_ROUTE,
    broker_config.TAG_PEDESTAL:          broker_config.DETECTOR_PEDESTAL_ROUTE,
    broker_config.TAG_POWER_ON:          broker_config.DETECTOR_PEDESTAL_ROUTE,
}



class RabbitMqClient:

    def __init__(self, broker_url=broker_config.DEFAULT_BROKER_URL):
        self.broker_url = broker_url
        self.connection = None
        self.channel = None


    def open(self):
        try:
            self.connection = BlockingConnection(ConnectionParameters(self.broker_url))
        except Exception:
            sleep(1)
            self.connection = BlockingConnection(ConnectionParameters(self.broker_url))

        self.channel = self.connection.channel()

        self.channel.exchange_declare(
            exchange=broker_config.REQUEST_EXCHANGE,
            exchange_type="topic"
        )

        self.channel.exchange_declare(
            exchange=broker_config.STATUS_EXCHANGE,
            exchange_type="fanout"
        )


    def close(self):
        self.connection.close()
        self.connection = None
        self.channel = None


    def send(self, write_request, tag):
        if self.channel is None:
            raise RuntimeError("RabbitMqClient not connected.")

        if tag.startswith("epics_"):
            routing_key = tag
        else:
            routing_key = ROUTES.get(tag, broker_config.DEFAULT_ROUTE)

        request_id = str(uuid.uuid4())
        body_bytes = json.dumps(write_request).encode()
        properties = BasicProperties(correlation_id=request_id)

        self.channel.basic_publish(
            exchange=broker_config.REQUEST_EXCHANGE,
            properties=properties,
            routing_key=routing_key,
            body=body_bytes
        )

        status_header = {
            "action": "write_request",
            "source": "BrokerClient",
            "routing_key": routing_key
        }
        properties = BasicProperties(headers=status_header, correlation_id=request_id)

        self.channel.basic_publish(
            exchange=broker_config.STATUS_EXCHANGE,
            properties=properties,
            routing_key=routing_key,
            body=body_bytes
        )



