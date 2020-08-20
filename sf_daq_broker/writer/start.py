import argparse
import json
import logging

from datetime import datetime
from functools import partial
from threading import Thread
from time import time, sleep
from pika import BlockingConnection, ConnectionParameters, BasicProperties

from sf_daq_broker import config, utils
import sf_daq_broker.rabbitmq.config as broker_config
from sf_daq_broker.writer.bsread_writer import write_from_imagebuffer, write_from_databuffer

_logger = logging.getLogger(__name__)


def audit_failed_write_request(write_request):

    original_output_file = write_request.get("output_file", "output_file_not_specified")
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

    data_api_request = request["data_api_request"]
    output_file = request["output_file"]
    run_log_file = request["run_log_file"]
    metadata = request["metadata"]
    request_timestamp = request["timestamp"]

    file_handler = None
    if run_log_file:
        file_handler = logging.FileHandler(run_log_file)
        file_handler.setLevel(logging.INFO)
        _logger.addHandler(file_handler)

    try:
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

        _logger.info("Starting download.")

        start_time = time()

        if channels[0]['backend'] == 'sf-imagebuffer':
            write_from_imagebuffer(data_api_request, output_file, metadata)
        else:
            write_from_databuffer(data_api_request, output_file, metadata)

        _logger.info("Finished. Took %s seconds to complete request." % (time() - start_time))

        _logger.removeHandler(file_handler)

    except Exception:
        audit_failed_write_request(request)
        raise

    finally:
        if file_handler:
            _logger.removeHandler(file_handler)


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


def confirm_request(channel, method_frame, body, output_file):
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    update_status(channel, body, "write_finished", output_file)


def reject_request(channel, method_frame, body, output_file, e):
    channel.basic_reject(delivery_tag=method_frame.delivery_tag,
                         requeue=False)

    update_status(channel, body, "write_rejected", output_file, str(e))


def on_broker_message(channel, method_frame, header_frame, body, connection):

    output_file = None

    try:
        request = json.loads(body.decode())

        output_file = request["output_file"]
        update_status(channel, body, "write_start", output_file)

        def process_async():
            try:
                process_request(request)

            except Exception as ex:
                _logger.exception("Error while trying to write a requested data.")

                reject_request_f = partial(reject_request, channel, method_frame, body, output_file, ex)
                connection.add_callback_threadsafe(reject_request_f)

            else:
                confirm_request_f = partial(confirm_request, channel, method_frame, body, output_file)
                connection.add_callback_threadsafe(confirm_request_f)

        thread = Thread(target=process_async)
        thread.daemon = True
        thread.start()

    except Exception as e:
        _logger.exception("Error while trying to write a requested data.")
        reject_request(channel, method_frame, body, output_file, e)


def start_service(broker_url):

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

    on_broker_message_f = partial(on_broker_message, connection=connection)
    channel.basic_consume(broker_config.BSREAD_QUEUE, on_broker_message_f)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()


def run():
    parser = argparse.ArgumentParser(description='Bsread data writer')

    parser.add_argument("--broker_url", default=broker_config.DEFAULT_BROKER_URL,
                        help="Address of the broker to connect to.")
    parser.add_argument("--data_retrieval_delay", default=config.DATA_RETRIEVAL_DELAY, type=int,
                        help="Time to wait before asking the data-api for the data.")
    parser.add_argument("--log_level", default="INFO",
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")
    parser.add_argument("--writer_id", default="writer",
                        help="Name of the writer for the logs")

    args = parser.parse_args()

    writer_id_format = '{%s}' % args.writer_id
    logs_format = '[%(levelname)s] %(message)s'
    logging.basicConfig(level=args.log_level, format=writer_id_format + logs_format)

    config.DATA_RETRIEVAL_DELAY = args.data_retrieval_delay

    start_service(broker_url=args.broker_url)


if __name__ == "__main__":
    run()
