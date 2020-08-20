import argparse
import json
import logging
import os

from datetime import datetime
from time import time, sleep
from pika import BlockingConnection, ConnectionParameters, BasicProperties

from sf_daq_broker import config, utils
import sf_daq_broker.rabbitmq.config as broker_config
from sf_daq_broker.writer.bsread_writer import write_from_imagebuffer, write_from_databuffer

_logger = logging.getLogger(__name__)


def audit_failed_write_request(data_api_request, original_output_file, metadata, timestamp):

    write_request = {
        "data_api_request": data_api_request,
        "output_file": original_output_file,
        "metadata": metadata,
        "timestamp": timestamp
    }

    output_file = original_output_file + ".err"

    try:
        current_time = datetime.now().strftime(config.AUDIT_FILE_TIME_FORMAT)

        with open(output_file, "w") as audit_file:
            audit_file.write("[%s] %s" % (current_time, json.dumps(write_request)))

    except Exception:
        _logger.exception("Error while trying to write request %s to file %s." % (write_request, output_file))


def wait_for_delay(request_timestamp):

    current_timestamp = time()
    # sleep time = target sleep time - time that has already passed.
    adjusted_retrieval_delay = config.DATA_RETRIEVAL_DELAY - (current_timestamp - request_timestamp)

    if adjusted_retrieval_delay < 0:
        adjusted_retrieval_delay = 0

    _logger.debug("Request timestamp=%s, current_timestamp=%s, adjusted_retrieval_delay=%s." %
                  (request_timestamp, current_timestamp, adjusted_retrieval_delay))

    _logger.info("Sleeping for %s seconds before continuing." % adjusted_retrieval_delay)
    sleep(adjusted_retrieval_delay)


def process_request(request):

    try:
        data_api_request = request["data_api_request"]
        output_file = request["output_file"]
        run_log_file = request["run_log_file"]
        metadata = request["metadata"]
        request_timestamp = request["timestamp"]

        _logger.info("Received request to write file %s from startPulseId=%s to endPulseId=%s" % (
            output_file,
            data_api_request["range"]["startPulseId"],
            data_api_request["range"]["endPulseId"]))

        if output_file == "/dev/null":
            _logger.info("Output file set to /dev/null. Skipping request.")
            return

        channels = data_api_request.get("channels")
        if not channels:
            _logger.info("No channels requested. Skipping request.")
            return

        if config.TRANSFORM_PULSE_ID_TO_TIMESTAMP_QUERY:
            data_api_request = utils.transform_range_from_pulse_id_to_timestamp(data_api_request)

        wait_for_delay(request_timestamp)

        start_time = time()

        if channels[0]['backend'] == 'sf-imagebuffer':
            write_from_imagebuffer(data_api_request, output_file, metadata)
        else:
            write_from_databuffer(data_api_request, output_file, metadata)

        end_time = time()
        _logger.info("Data writing took %s seconds. (DATA_API3)" % (end_time - start_time))

    except Exception:
        audit_failed_write_request(request)
        raise


def update_status(channel, body, action, file, message=None):

    status_header = {
        "action": action,
        "source": "bsread_writer",
        "routing_key": broker_config.BSREAD_QUEUE,
        "file": file,
        "message": message
    }

    channel.basic_publish(exchange=broker_config.STATUS_EXCHANGE,
                          properties=BasicProperties(
                              headers=status_header),
                          routing_key="",
                          body=body)


def on_broker_message(channel, method_frame, header_frame, body):

    output_file = None

    try:
        request = json.loads(body.decode())

        output_file = request["output_file"]
        update_status(channel, body, "write_start", output_file)

        process_request(request)

    except Exception as e:

        _logger.exception("Error while trying to write a requested data.")

        channel.basic_reject(delivery_tag=method_frame.delivery_tag,
                             requeue=True)

        update_status(channel, body, "write_rejected", output_file, str(e))

    else:
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

        update_status(channel, body, "write_finished", output_file)


def start_service(broker_url, user_id):

    if user_id != -1:
        _logger.info("Setting bsread writer uid and gid to %s.", user_id)
        os.setgid(user_id)
        os.setuid(user_id)

    else:
        _logger.info("Not changing process uid and gid.")

    connection = BlockingConnection(ConnectionParameters(broker_url))
    channel = connection.channel()

    channel.exchange_declare(exchange=broker_config.STATUS_EXCHANGE,
                             exchange_type="fanout")
    channel.exchange_declare(exchange=broker_config.REQUEST_EXCHANGE,
                             exchange_type="topic")

    channel.queue_declare(queue=broker_config.BSREAD_QUEUE, auto_delete=True)
    channel.queue_bind(queue=broker_config.BSREAD_QUEUE,
                       exchange=broker_config.REQUEST_EXCHANGE,
                       routing_key="*.%s.*" % broker_config.BSREAD_QUEUE)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(broker_config.BSREAD_QUEUE, on_broker_message)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()


def run():
    parser = argparse.ArgumentParser(description='Bsread data writer')

    parser.add_argument("--broker_url", default=broker_config.DEFAULT_BROKER_URL,
                        help="Address of the broker to connect to.")
    parser.add_argument("--user_id", type=int, default=-1,
                        help="user_id under which to run the writer process. Use -1 for current user.")
    parser.add_argument("--data_retrieval_delay", default=config.DEFAULT_DATA_RETRIEVAL_DELAY, type=int,
                        help="Time to wait before asking the data-api for the data.")
    parser.add_argument("--log_level", default="INFO",
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")

    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format='[%(levelname)s] %(message)s')

    config.DEFAULT_DATA_RETRIEVAL_DELAY = args.data_retrieval_delay

    start_service(broker_url=args.broker_url,
                  user_id=args.user_id)


if __name__ == "__main__":
    run()
