import argparse
import json
import logging
from datetime import datetime
from functools import partial
from threading import Thread
from time import sleep, time

from pika import BasicProperties, BlockingConnection, ConnectionParameters

import sf_daq_broker.rabbitmq.config as broker_config
from sf_daq_broker import config
from sf_daq_broker.detector.pedestal import take_pedestal
from sf_daq_broker.detector.power_on_detector import power_on_detector
from sf_daq_broker.rabbitmq.msg_broker_client import RabbitMqClient
from sf_daq_broker.utils import get_data_api_request, get_writer_request, json_save, json_load
from sf_daq_broker.writer.bsread_writer import write_from_databuffer_api3, write_from_imagebuffer
from sf_daq_broker.writer.detector_writer import detector_retrieve


_logger = logging.getLogger("broker_writer")



def audit_failed_write_request(write_request):
    original_output_file = write_request.get("output_file", None)
    if not original_output_file:
        return

    output_file = original_output_file + ".err"

    try:
        current_time = datetime.now().strftime(config.AUDIT_FILE_TIME_FORMAT)

        with open(output_file, "w") as audit_file:
            pretty_write_request = json.dumps(write_request)
            audit_file.write(f"[{current_time}] {pretty_write_request}")

    except Exception:
        _logger.exception(f"Error while trying to write request {write_request} to file {output_file}.")


def wait_for_delay(request_timestamp, writer_type):
    if request_timestamp is None:
        return

    time_to_wait = config.BSDATA_RETRIEVAL_DELAY
    if writer_type == broker_config.TAG_DETECTOR_RETRIEVE:
        time_to_wait = config.DETECTOR_RETRIEVAL_DELAY

#    # should not come here in this case, since request_timestamp is None
#    if writer_type == broker_config.TAG_PEDESTAL or writer_type != broker_config.TAG_POWER_ON:
#        time_to_wait = 0

    current_timestamp = time()
    # sleep time = target sleep time - time that has already passed.
    adjusted_retrieval_delay = time_to_wait - (current_timestamp - request_timestamp)
    adjusted_retrieval_delay = max(adjusted_retrieval_delay, 0)

    _logger.debug(f"Request timestamp={request_timestamp}, current_timestamp={current_timestamp}, adjusted_retrieval_delay={adjusted_retrieval_delay}.")
    _logger.info(f"Sleeping for {adjusted_retrieval_delay} seconds before continuing.")
    sleep(adjusted_retrieval_delay)


def process_request(request, broker_client):
    writer_type = request["writer_type"]
    channels = request.get("channels", None)

    start_pulse_id = request.get("start_pulse_id", 0)
    stop_pulse_id = request.get("stop_pulse_id", 100)

    output_file = request.get("output_file", None)
    run_log_file = request.get("run_log_file", None)

    metadata = request.get("metadata", None)
    request_timestamp = request.get("timestamp", None)

    file_handler = None
    if run_log_file:
        file_handler = logging.FileHandler(run_log_file)
        file_handler.setLevel(logging.INFO)
        _logger.addHandler(file_handler)

        logger_data_api = None
        if writer_type in (broker_config.TAG_DATA3BUFFER, broker_config.TAG_IMAGEBUFFER):
            logger_data_api = logging.getLogger("data_api3")
            logger_data_api.addHandler(file_handler)

    try:
        _logger.info(f"Request for {writer_type} : output_file {output_file} from pulse_id {start_pulse_id} to {stop_pulse_id}")

        if output_file == "/dev/null":
            _logger.info("Output file set to /dev/null. Skipping request.")
            return

        if not channels and writer_type not in (broker_config.TAG_PEDESTAL, broker_config.TAG_POWER_ON):
            _logger.info("No channels requested. Skipping request.")
            return

        wait_for_delay(request_timestamp, writer_type)

        _logger.info("Starting payload.")

        start_time = time()

        if writer_type == broker_config.TAG_DATA3BUFFER:
            _logger.info("Using data_api3 databuffer writer.")
            write_from_databuffer_api3(get_data_api_request(channels, start_pulse_id, stop_pulse_id), output_file, metadata)

        elif writer_type == broker_config.TAG_IMAGEBUFFER:
            _logger.info("Using imagebuffer writer.")
            write_from_imagebuffer(get_data_api_request(channels, start_pulse_id, stop_pulse_id), output_file, metadata)

        elif writer_type == broker_config.TAG_PEDESTAL:
            _logger.info("Doing pedestal.")

            detectors = request.get("detectors", [])
            rate_multiplicator = request.get("rate_multiplicator", 1)
            det_start_pulse_id, det_stop_pulse_id = take_pedestal(detectors_name=detectors, rate=rate_multiplicator)

            # overwrite start/stop pulse_ids in run_info json file
            run_file_json = request.get("run_file_json", None)
            if run_file_json is not None:
                run_info = json_load(run_file_json)

                run_info["start_pulseid"] = det_start_pulse_id
                run_info["stop_pulseid"]  = det_stop_pulse_id

                json_save(run_info, run_file_json)

            request_det_retrieve = {
                "det_start_pulse_id" : det_start_pulse_id,
                "det_stop_pulse_id"  : det_stop_pulse_id,
                "rate_multiplicator" : request.get("rate_multiplicator", 1),
                "run_file_json"      : request.get("run_file_json", None),
                "path_to_pgroup"     : request.get("path_to_pgroup", None),
                "run_info_directory" : request.get("run_info_directory", None),
                "directory_name"     : request.get("directory_name"),
                "request_time"       : request.get("request_time", str(datetime.now()))
            }

            broker_client.open()

            for detector in detectors:
                request_det_retrieve["detector_name"] = detector
                request_det_retrieve["detectors"] = {}
                request_det_retrieve["detectors"][detector] = {}

                output_file_prefix = request.get("output_file_prefix", "/tmp/error")
                output_file_det = f"{output_file_prefix}.{detector}.h5"
                run_log_file_det = run_log_file[:-4] + "." + detector + ".log"

                write_request = get_writer_request(
                    writer_type=broker_config.TAG_DETECTOR_RETRIEVE,
                    channels=request_det_retrieve,
                    output_file=output_file_det,
                    metadata=None,
                    start_pulse_id=det_start_pulse_id,
                    stop_pulse_id=det_start_pulse_id,
                    run_log_file=run_log_file_det
                )

                broker_client.send(write_request, broker_config.TAG_DETECTOR_RETRIEVE)

            broker_client.close()

        elif writer_type == broker_config.TAG_POWER_ON:
            _logger.info("Power ON detector")
            detector_name = request.get("detector_name", None)
            beamline = request.get("beamline", None)
            power_on_detector(detector_name=detector_name, beamline=beamline)

        elif writer_type == broker_config.TAG_DETECTOR_RETRIEVE:
            _logger.info("Using detector retrieve writer.")
            detector_retrieve(channels, output_file)

        elif writer_type == broker_config.TAG_DETECTOR_CONVERT:
            _logger.info("Using detector convert writer.")
            #TODO: nothing here?

        delta_time = time() - start_time
        _logger.info(f"Finished. Took {delta_time} seconds to complete request.")

#        #TODO this block is also in finally, it will run there anyway
#        if file_handler:
#            _logger.removeHandler(file_handler)
#            if logger_data_api is not None:
#                logger_data_api.removeHandler(file_handler)

    except Exception:
        audit_failed_write_request(request)
        _logger.exception(f"Request failed: {request}")
        raise

    finally:
        if file_handler:
            _logger.removeHandler(file_handler)
            if logger_data_api is not None:
                logger_data_api.removeHandler(file_handler)


def update_status(channel, body, action, file, message=None):
    status_header = {
        "action": action,
        "source": "bsread_writer",
        "routing_key": "*",
        "file": file,
        "message": message
    }

    channel.basic_publish(
        exchange=broker_config.STATUS_EXCHANGE,
        properties=BasicProperties(headers=status_header),
        routing_key="",
        body=body
    )


def confirm_request(channel, method_frame, body, output_file):
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)
    update_status(channel, body, "write_finished", output_file)


def reject_request(channel, method_frame, body, output_file, e):
    channel.basic_reject(delivery_tag=method_frame.delivery_tag, requeue=False)
    update_status(channel, body, "write_rejected", output_file, str(e))


def on_broker_message(channel, method_frame, _header_frame, body, connection, broker_client):
    try:
        request = json.loads(body.decode())

        output_file = request.get("output_file", None)
        update_status(channel, body, "write_start", output_file)

        def process_async():
            try:
                process_request(request, broker_client)

            except Exception as e:
                _logger.exception("Error while trying to write a requested data.")
                callback = partial(reject_request, channel, method_frame, body, output_file, e)

            else:
                callback = partial(confirm_request, channel, method_frame, body, output_file)

            connection.add_callback_threadsafe(callback)

        thread = Thread(target=process_async)
        thread.daemon = True
        thread.start()

    except Exception as e:
        _logger.exception("Error while trying to write a requested data.")
        reject_request(channel, method_frame, body, output_file, e)


def start_service(broker_url, writer_type=0):
    connection = BlockingConnection(ConnectionParameters(broker_url))
    channel = connection.channel()

    channel.exchange_declare(exchange=broker_config.STATUS_EXCHANGE,  exchange_type="fanout")
    channel.exchange_declare(exchange=broker_config.REQUEST_EXCHANGE, exchange_type="topic")

    #TODO: should introduce named writer_types / enum?

    ROUTING_KEYS = {
        1: broker_config.DETECTOR_RETRIEVE_ROUTE,
        2: broker_config.DETECTOR_CONVERSION_ROUTE,
        3: broker_config.DETECTOR_PEDESTAL_ROUTE
    }

    REQUEST_QUEUES = {
        1: broker_config.DETECTOR_RETRIEVE_QUEUE,
        2: broker_config.DETECTOR_CONVERSION_QUEUE,
        3: broker_config.DETECTOR_PEDESTAL_QUEUE
    }

    routing_key   = ROUTING_KEYS.get(writer_type, broker_config.DEFAULT_ROUTE)
    request_queue = REQUEST_QUEUES.get(writer_type, broker_config.DEFAULT_QUEUE)

    channel.queue_declare(queue=request_queue, auto_delete=True)
    channel.queue_bind(queue=request_queue, exchange=broker_config.REQUEST_EXCHANGE, routing_key=routing_key)
    channel.basic_qos(prefetch_count=1)

    broker_client = RabbitMqClient(broker_url=broker_url)

    on_broker_message_cb = partial(on_broker_message, connection=connection, broker_client=broker_client)
    channel.basic_consume(request_queue, on_broker_message_cb)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()


def run():
    parser = argparse.ArgumentParser(description="data writer")

    parser.add_argument("--broker_url", default=broker_config.DEFAULT_BROKER_URL, help="Address of the broker to connect to.")
    parser.add_argument("--log_level", default="INFO", choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"], help="Log level to use.")
    parser.add_argument("--writer_id", default=1, type=int, help="Id of the writer")
    parser.add_argument("--writer_type", default=0, type=int, help="Type of the writer (0-epics/bs/camera; 1 - detector retrieve; 2 - detector conversion; 3 - pedestal)")

    clargs = parser.parse_args()

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(clargs.log_level)
    formatter = logging.Formatter(f"[%(levelname)s] (broker_writer_{clargs.writer_id}_{clargs.writer_type}) %(message)s")
    stream_handler.setFormatter(formatter)

    _logger.setLevel(clargs.log_level)
    _logger.addHandler(stream_handler)

    for logger_name in ["data_api", "data_api3"]:
        logger_data_api = logging.getLogger(logger_name)
        logger_data_api.setLevel(clargs.log_level)
        logger_data_api.addHandler(stream_handler)

    # make message-broker less noisy in logs
    logging.getLogger("pika").setLevel(logging.WARNING)

    _logger.info("Writer started. Waiting for requests.")

    start_service(broker_url=clargs.broker_url, writer_type=clargs.writer_type)





if __name__ == "__main__":
    run()



