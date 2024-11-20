import argparse
from datetime import datetime

from pika import BlockingConnection, ConnectionParameters

from sf_daq_broker.rabbitmq import broker_config
from sf_daq_broker.utils import json_str_to_obj


COLORS = {
    "red":     "\x1b[31;1m",
    "green":   "\x1b[32;1m",
    "yellow":  "\x1b[33;1m",
    "blue":    "\x1b[34;1m",
    "magenta": "\x1b[35;1m"
}

COLOR_END_MARKER = "\x1b[0m"

COLOR_MAPPING = {
    # sf-daq writers
    "write_request":   "blue",
    "write_start":     "yellow",
    "write_finished":  "green",
    "write_rejected":  "red",
    # epics buffer
    "request_start":   "yellow",
    "request_success": "green",
    "request_fail":    "red"
}



def run():
    parser = argparse.ArgumentParser(description="connect and listen to broker events")
    parser.add_argument("--broker_url", default=broker_config.DEFAULT_BROKER_URL, help="RabbitMQ broker URL")

    clargs = parser.parse_args()
    connect_to_broker(broker_url=clargs.broker_url)


def connect_to_broker(broker_url):
    params = ConnectionParameters(broker_url)
    connection = BlockingConnection(params)

    channel = connection.channel()
    channel.exchange_declare(exchange=broker_config.STATUS_EXCHANGE, exchange_type="fanout")
    queue = channel.queue_declare(queue="", exclusive=True).method.queue
    channel.queue_bind(queue=queue, exchange=broker_config.STATUS_EXCHANGE)
    channel.basic_consume(queue, on_status)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()


def on_status(_channel, _method_frame, header_frame, body):
    header = header_frame.headers
    body = body.decode()
    request = json_str_to_obj(body)

    action = header["action"]
    source = header["source"]

    action_output = colorize(action)
    time_output = datetime.now().strftime("%Y%m%d-%H:%M:%S.%f")

    print(f"[{time_output}] {action_output} {source}")
    print(request)


def colorize(action):
    color_name = COLOR_MAPPING.get(action, "magenta")
    color = COLORS[color_name]
    return f"{color}{action}{COLOR_END_MARKER}"





if __name__ == "__main__":
    run()



