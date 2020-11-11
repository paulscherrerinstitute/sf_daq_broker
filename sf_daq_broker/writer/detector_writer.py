import logging

from sf_daq_broker.detector.buffer_reader import DetectorReader
from sf_daq_broker.detector.image_assembler import ImageAssembler
from sf_daq_broker.detector.ram_buffer import RamBuffer

_logger = logging.getLogger("broker_writer")

try:
    import ujson as json
except:
    _logger.warning("There is no ujson in this environment. Performance will suffer.")
    import json


def write_from_detectorbuffer(data_api_request, output_file, metadata):
    _logger.debug("Data API request: %s", data_api_request)

    detector_folder = "/tmp/det"
    output_file = "output_file"
    n_modules = 16
    n_slots = 100
    start_pulse_id = 0
    end_pulse_id = 200

    ram_buffer = RamBuffer(n_modules=n_modules,
                           n_slots=n_slots)

    detector_reader = DetectorReader(ram_buffer=ram_buffer,
                                     detector_folder=detector_folder,
                                     n_modules=n_modules)
    detector_reader.start_reading(start_pulse_id=start_pulse_id,
                                  end_pulse_id=end_pulse_id)

    image_assembler = ImageAssembler(ram_buffer=ram_buffer,
                                     n_modules=n_modules)

    detector_writer = DetectorWriter(output_file=output_file)

    for pulse_id in range(start_pulse_id, end_pulse_id):
        meta_buffer, data_buffer = image_assembler.get_data(pulse_id)
        detector_writer.write(pulse_id, meta_buffer, data_buffer)

    detector_reader.close()


class DetectorWriter(object):
    def __init__(self, output_file):
        self.output_file = output_file

    def write(self, pulse_id, meta_buffer, data_buffer):
        pass
