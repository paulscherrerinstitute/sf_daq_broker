import argparse
import json
from datetime import datetime

from pika import BlockingConnection, ConnectionParameters

from . import broker_config


COLOR_MAPPING = {
    "write_request": "\x1b[34;1m",
    "write_start": "\x1b[1;33;1m",
    "write_finished": "\x1b[1;32;1m"
}

COLOR_END_MARKER = "\x1b[0m"



def colorize(action):
    color = COLOR_MAPPING.get(action, "")
    return f"{color}{action}{COLOR_END_MARKER}"


def on_status(_channel, _method_frame, header_frame, body):
    header = header_frame.headers
    body = body.decode()
    request = json.loads(body)

    action = header["action"]
    source = header["source"]

    action_output = colorize(action)
    time_output = datetime.utcnow().strftime("%Y%m%d-%H:%M:%S.%f")

    print(f"[{time_output}] {action_output} {source}")
    print(request)


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



def main():
    parser = argparse.ArgumentParser(description="Connect and listen to broker events.")
    parser.add_argument("--broker_url", default=broker_config.DEFAULT_BROKER_URL, help="RabbitMQ broker URL")

    clargs = parser.parse_args()
    connect_to_broker(broker_url=clargs.broker_url)





if __name__ == "__main__":
    main()



