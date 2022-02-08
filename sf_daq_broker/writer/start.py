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
from sf_daq_broker.utils import get_data_api_request
from sf_daq_broker.writer.bsread_writer import write_from_imagebuffer, write_from_databuffer, write_from_databuffer_api3
from sf_daq_broker.writer.epics_writer import write_epics_pvs
from sf_daq_broker.detector.pedestal import take_pedestal
from sf_daq_broker.writer.detector_writer import detector_retrieve
from sf_daq_broker.detector.power_on_detector import power_on_detector

_logger = logging.getLogger("broker_writer")


def audit_failed_write_request(write_request):

    original_output_file = write_request.get("output_file", None)
    if original_output_file is None:
        return

    output_file = original_output_file + ".err"

    try:
        current_time = datetime.now().strftime(config.AUDIT_FILE_TIME_FORMAT)

        with open(output_file, "w") as audit_file:
            audit_file.write("[%s] %s" % (current_time, json.dumps(write_request)))

    except Exception:
        _logger.exception("Error while trying to write request %s to file %s." % (write_request, output_file))


def wait_for_delay(request_timestamp, writer_type):

    if request_timestamp is None:
        return

    time_to_wait = config.BSDATA_RETRIEVAL_DELAY
    if writer_type == broker_config.TAG_DETECTOR_RETRIEVE:
        time_to_wait = config.DETECTOR_RETRIEVAL_DELAY

# should not come here in this case, since request_timestamp is None
#    if writer_type == broker_config.TAG_PEDESTAL or writer_type != broker_config.TAG_POWER_ON:
#        time_to_wait = 0

    current_timestamp = time()
    # sleep time = target sleep time - time that has already passed.
    adjusted_retrieval_delay = time_to_wait - (current_timestamp - request_timestamp)

    if adjusted_retrieval_delay < 0:
        adjusted_retrieval_delay = 0

    _logger.debug("Request timestamp=%s, current_timestamp=%s, adjusted_retrieval_delay=%s." %
                  (request_timestamp, current_timestamp, adjusted_retrieval_delay))

    _logger.info("Sleeping for %s seconds before continuing." % adjusted_retrieval_delay)
    sleep(adjusted_retrieval_delay)


def process_request(request):

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

        if writer_type == broker_config.TAG_DATABUFFER:
            logger_data_api = logging.getLogger("data_api")
        elif writer_type == broker_config.TAG_DATA3BUFFER:
            logger_data_api = logging.getLogger("data_api3")
        elif writer_type == broker_config.TAG_IMAGEBUFFER:
            logger_data_api = logging.getLogger("data_api3")
        elif writer_type == broker_config.TAG_EPICS:
            logger_data_api = logging.getLogger("data_api")

        if logger_data_api is not None:
            logger_data_api.addHandler(file_handler)

    try:
        _logger.info("Request for %s : output_file %s from pulse_id %s to %s" %
                     (writer_type, output_file, start_pulse_id, stop_pulse_id))

        if output_file == "/dev/null":
            _logger.info("Output file set to /dev/null. Skipping request.")
            return

        if not channels and ( writer_type != broker_config.TAG_PEDESTAL and writer_type != broker_config.TAG_POWER_ON):
            _logger.info("No channels requested. Skipping request.")
            return

        wait_for_delay(request_timestamp, writer_type)

        _logger.info("Starting download.")

        start_time = time()

        if writer_type == broker_config.TAG_DATABUFFER:
            _logger.info("Using databuffer writer.")
            write_from_databuffer(get_data_api_request(channels, start_pulse_id, stop_pulse_id), output_file, metadata)

        elif writer_type == broker_config.TAG_DATA3BUFFER:
            _logger.info("Using data_api3 databuffer writer.")
            write_from_databuffer_api3(get_data_api_request(channels, start_pulse_id, stop_pulse_id), output_file, metadata)

        elif writer_type == broker_config.TAG_IMAGEBUFFER:
            _logger.info("Using imagebuffer writer.")
            write_from_imagebuffer(get_data_api_request(channels, start_pulse_id, stop_pulse_id), output_file, metadata)

        elif writer_type == broker_config.TAG_EPICS:
            _logger.info("Using epics writer.")
            write_epics_pvs(output_file, start_pulse_id, stop_pulse_id, metadata, channels)

        elif writer_type == broker_config.TAG_PEDESTAL:
            _logger.info("Doing pedestal.")
            detectors = request.get("detectors", [])
            det_start_pulse_id, det_stop_pulse_id = take_pedestal(detectors_name=detectors, rate=request.get("rate_multiplicator", 1))
            # overwrite start/stop pulse_id's in run_info json file
            run_file_json = request.get("run_file_json", None)
            if run_file_json is not None:
                with open(run_file_json, "r") as request_json_file:
                    run_info = json.load(request_json_file)
                run_info["start_pulseid"] = det_start_pulse_id
                run_info["stop_pulseid"]  = det_stop_pulse_id
                with open(run_file_json, "w") as request_json_file:
                    json.dump(run_info, request_json_file, indent=2)

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
            
            for detector in detectors:
                request_det_retrieve["detector_name"] = detector
                request_det_retrieve["detectors"] = {}
                request_det_retrieve["detectors"][detector] = {}
                output_file_prefix = request.get("output_file_prefix", "/tmp/error")
                output_file_det = f'{output_file_prefix}.{detector}.h5'
                try:
                    detector_retrieve(request_det_retrieve, output_file_det)
                except Exception as ex:
                    _logger.exception("Error while trying to retrieve and convert pedestal data")
                    sleep(120)
                    try:
                        detector_retrieve(request_det_retrieve, output_file_det)
                    except Exception as ex2:
                        _logger.exception("(second attempt) Error while trying to retrieve and convert pedestal data") 
                    
             

        elif writer_type == broker_config.TAG_POWER_ON:
            _logger.info("Power ON detector")
            power_on_detector(detector_name=request.get("detector_name", None), beamline=request.get("beamline", None))

        elif writer_type == broker_config.TAG_DETECTOR_RETRIEVE:
            _logger.info("Using detector retrieve writer.")
            detector_retrieve(channels, output_file)

        elif writer_type == broker_config.TAG_DETECTOR_CONVERT:
            _logger.info("Using detector convert writer.")

        _logger.info("Finished. Took %s seconds to complete request." % (time() - start_time))

        if file_handler:
            _logger.removeHandler(file_handler)
            if logger_data_api is not None:
                logger_data_api.removeHandler(file_handler)

    except Exception:
        audit_failed_write_request(request)
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

    try:
        request = json.loads(body.decode())

        output_file = request.get("output_file", None)
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


def start_service(broker_url, writer_type=0):

    connection = BlockingConnection(ConnectionParameters(broker_url))
    channel = connection.channel()

    channel.exchange_declare(exchange=broker_config.STATUS_EXCHANGE,
                             exchange_type="fanout")
    channel.exchange_declare(exchange=broker_config.REQUEST_EXCHANGE,
                             exchange_type="topic")

    routing_key   = broker_config.DEFAULT_ROUTE
    request_queue = broker_config.DEFAULT_QUEUE
    if writer_type == 1:
        routing_key   = broker_config.DETECTOR_RETRIEVE_ROUTE
        request_queue = broker_config.DETECTOR_RETRIEVE_QUEUE
    if writer_type == 2:
        routing_key   = broker_config.DETECTOR_CONVERSION_ROUTE
        request_queue = broker_config.DETECTOR_CONVERSION_QUEUE
    if writer_type == 3:
        routing_key   = broker_config.DETECTOR_PEDESTAL_ROUTE
        request_queue = broker_config.DETECTOR_PEDESTAL_QUEUE
 
    channel.queue_declare(queue=request_queue, auto_delete=True)
    channel.queue_bind(queue=request_queue,
                       exchange=broker_config.REQUEST_EXCHANGE,
                       routing_key=routing_key)

    channel.basic_qos(prefetch_count=1)

    on_broker_message_f = partial(on_broker_message, connection=connection)
    channel.basic_consume(request_queue, on_broker_message_f)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()


def run():
    parser = argparse.ArgumentParser(description='data writer')

    parser.add_argument("--broker_url", default=broker_config.DEFAULT_BROKER_URL,
                        help="Address of the broker to connect to.")
    parser.add_argument("--log_level", default="INFO",
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")
    parser.add_argument("--writer_id", default=1, type=int,
                        help="Id of the writer")
    parser.add_argument("--writer_type", default=0, type=int,
                        help="Type of the writer (0-epics/bs/camera; 1 - detector retrieve; 2 - detector conversion; 3 - pedestal)")

    args = parser.parse_args()

# Logging formating:
    _logger.setLevel(args.log_level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(args.log_level)
    formatter = logging.Formatter(f'[%(levelname)s] (broker_writer_{args.writer_id}_{args.writer_type}) %(message)s')
    stream_handler.setFormatter(formatter)

    _logger.setLevel(args.log_level)
    _logger.addHandler(stream_handler)

    for logger_name in ["data_api", "data_api3"]:
        logger_data_api = logging.getLogger(logger_name)    
        logger_data_api.setLevel(args.log_level)
        logger_data_api.addHandler(stream_handler)

# make message-broker less noisy in logs
    logging.getLogger("pika").setLevel(logging.WARNING)

    _logger.info("Writer started. Waiting for requests.")

    start_service(broker_url=args.broker_url, writer_type=args.writer_type)


if __name__ == "__main__":
    run()
