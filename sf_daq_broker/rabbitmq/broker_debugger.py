import json
from datetime import datetime

from pika import BlockingConnection, ConnectionParameters

import sf_daq_broker.rabbitmq.config as broker_config

COLOR_END_MARKER = "\x1b[0m"


def get_color_for_action(action):

    color_mapping = {
        "write_request": "\x1b[34;1m",
        "write_start": "\x1b[1;33;1m",
        "write_finished": "\x1b[1;32;1m"
    }

    return color_mapping.get(action, "")


def on_status(_channel, _method_frame, header_frame, body):
    header = header_frame.headers
    request = json.loads(body.decode())

    action = header["action"]
    source = header["source"]

    action_output = get_color_for_action(action) + action + COLOR_END_MARKER
    time_output = datetime.utcnow().strftime("%Y%m%d-%H:%M:%S.%f")

    print(f"[{time_output}] {action_output} {source}")
    print(request)


def connect_to_broker(broker_url):
    connection = BlockingConnection(ConnectionParameters(broker_url))
    channel = connection.channel()

    channel.exchange_declare(exchange=broker_config.STATUS_EXCHANGE,
                             exchange_type="fanout")
    queue = channel.queue_declare(queue="", exclusive=True).method.queue
    channel.queue_bind(queue=queue,
                       exchange=broker_config.STATUS_EXCHANGE)

    channel.basic_consume(queue, on_status)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Connect and listen to broker events.")

    parser.add_argument("--broker_url", dest="broker_url",
                        default=broker_config.DEFAULT_BROKER_URL,
                        help="RabbitMQ broker URL")

    args = parser.parse_args()

    connect_to_broker(broker_url=args.broker_url)


if __name__ == "__main__":
    main()
