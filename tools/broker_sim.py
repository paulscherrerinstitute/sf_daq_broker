import itertools
import random
from collections import defaultdict
from threading import Thread
from time import sleep, time

from sf_daq_broker.rabbitmq import BrokerClient, broker_config
from sf_daq_broker.writer import start
from sf_daq_broker.writer.start import _logger, wait_for_delay, run as start_process


TAGS = (
    broker_config.TAG_DATA3BUFFER,
    broker_config.TAG_IMAGEBUFFER,
    broker_config.TAG_DETECTOR_CONVERT,
    broker_config.TAG_DETECTOR_PEDESTAL,
    broker_config.TAG_DETECTOR_POWER_ON,
    broker_config.TAG_DETECTOR_RETRIEVE
)


def process_request_internal(request, broker_client):
    writer_type = request["writer_type"]

#    channels          = request.get("channels", None)
#    start_pulse_id    = request.get("start_pulse_id", 0)
#    stop_pulse_id     = request.get("stop_pulse_id", 100)
#    output_file       = request.get("output_file", None)
#    metadata          = request.get("metadata", None)
    request_timestamp = request.get("timestamp", None)

#    _logger.info(f"request for writer type {writer_type}: output file {output_file} from pulse ID {start_pulse_id} to {stop_pulse_id}")
    _logger.info(f"request for writer type {writer_type}")

#    if output_file == "/dev/null":
#        _logger.info("skipping request: output file is /dev/null")
#        return

#    if not channels and writer_type not in (broker_config.TAG_DETECTOR_PEDESTAL, broker_config.TAG_DETECTOR_POWER_ON):
#        _logger.info("skipping request: no channels requested")
#        return

    wait_for_delay(request_timestamp, writer_type)

    start_time = time()

    sleep(random.random() * 5)

    # fail in 1/3 cases
    if not random.randint(0, 2):
        raise RuntimeError("Divide By Cucumber")

    delta_time = time() - start_time
    _logger.info(f"processing request took {delta_time} seconds")



# overwrite with modified
start.process_request_internal = process_request_internal
start.ROUTING_KEYS = defaultdict(lambda: "#") # any key



def start_send():
    thread = Thread(target=send)
    thread.daemon = True
    thread.start()


def send():
    sleep(3)

    broker_client = BrokerClient(broker_url=broker_config.DEFAULT_BROKER_URL)

    for counter in itertools.count():
        sleep(random.random() * 5)

        tag = random.choice(TAGS)

        #TODO: fill request
        request = {
#            "channels": None,
#            "detectors": detectors,
#            "directory_name": directory_name,
#            "metadata": None,
#            "output_file": None,
#            "output_file_prefix": f"{full_path}/{pedestal_name}",
#            "path_to_pgroup": path_to_pgroup,
#            "pedestalmode": pedestalmode,
#            "rate_multiplicator": rate_multiplicator,
#            "request_time": str(request_time),
#            "run_file_json": run_file_json,
#            "run_info_directory": run_info_directory,
#            "run_log_file": f"{run_info_directory}/{pedestal_name}.log",
#            "start_pulse_id": 0,
#            "stop_pulse_id": 100,
#            "timestamp": None,
            "writer_type": tag
        }

        _logger.info(f"send {counter}: {tag}")
        broker_client.open()
        broker_client.send(request, tag)
        broker_client.close()
        _logger.info(f"sent {counter}: {tag}")





if __name__ == "__main__":
    _logger.info("start send")
    start_send()
    _logger.info("start process")
    start_process()


