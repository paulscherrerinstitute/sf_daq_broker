import uuid
from time import sleep

from pika import BasicProperties, BlockingConnection, ConnectionParameters

from sf_daq_broker.utils import json_obj_to_str

from . import broker_config


ROUTES = {
    broker_config.TAG_DATA3BUFFER:       broker_config.ROUTE_DATA_API,
    broker_config.TAG_IMAGEBUFFER:       broker_config.ROUTE_DATA_API,
    broker_config.TAG_DETECTOR_RETRIEVE: broker_config.ROUTE_DETECTOR_RETRIEVE,
    broker_config.TAG_DETECTOR_CONVERT:  broker_config.ROUTE_DETECTOR_CONVERT,
    broker_config.TAG_DETECTOR_PEDESTAL: broker_config.ROUTE_DETECTOR_PEDESTAL,
    broker_config.TAG_DETECTOR_POWER_ON: broker_config.ROUTE_DETECTOR_PEDESTAL,
}



class BrokerClient:

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
            raise RuntimeError("BrokerClient not connected.")

        if tag.startswith("epics_"):
            routing_key = tag
        else:
            routing_key = ROUTES[tag]

        correlation_id = str(uuid.uuid4())
        body_bytes = json_obj_to_str(write_request).encode()
        properties = BasicProperties(correlation_id=correlation_id)

        self.channel.basic_publish(
            exchange=broker_config.REQUEST_EXCHANGE,
            properties=properties,
            routing_key=routing_key,
            body=body_bytes
        )

        headers = {
            "action": "write_request",
            "source": "BrokerClient",
            "routing_key": routing_key
        }

        properties = BasicProperties(
            headers=headers,
            correlation_id=correlation_id
        )

        self.channel.basic_publish(
            exchange=broker_config.STATUS_EXCHANGE,
            properties=properties,
            routing_key=routing_key,
            body=body_bytes
        )



