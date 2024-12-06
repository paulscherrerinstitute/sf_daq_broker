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
    "magenta": "\x1b[35;1m",
    "cyan":    "\x1b[36;1m"
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
    BrokerDebugger(broker_url=clargs.broker_url)



class BrokerDebugger:

    def __init__(self, broker_url):
        connection = BlockingConnection(ConnectionParameters(broker_url))

        channel = connection.channel()
        channel.exchange_declare(exchange=broker_config.STATUS_EXCHANGE, exchange_type="fanout")

        queue = channel.queue_declare(queue="", exclusive=True).method.queue
        channel.queue_bind(queue=queue, exchange=broker_config.STATUS_EXCHANGE)
        channel.basic_consume(queue, self.on_status, auto_ack=True)

        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()


    def on_status(self, _channel, method_frame, header_frame, body):
        correlation_id = header_frame.correlation_id
        headers        = header_frame.headers
        timestamp      = header_frame.timestamp

        body = body.decode()
        request = json_str_to_obj(body)

        writer_type = request.get("writer_type")

        action = headers["action"]
        source = headers["source"]
        message = headers.get("message")

        color = COLOR_MAPPING.get(action, "cyan")
        colored_action = colorize(action, color)

        timestamp_msg = datetime.fromtimestamp(timestamp / 1e9)
        timestamp_now = datetime.now()
        time_delta = timestamp_now - timestamp_msg

        print(f"[{timestamp_now}]", f"[{timestamp_msg}]", time_delta, correlation_id, colored_action, source, writer_type)

        if message:
            print(colorize(message, "magenta"))

#        print("  Frame:  ", method_frame)
#        print("  Headers:", headers)
#        print("  Request:", request)
#        print()



def colorize(string, color):
    color_marker = COLORS[color]
    return f"{color_marker}{string}{COLOR_END_MARKER}"





if __name__ == "__main__":
    run()



