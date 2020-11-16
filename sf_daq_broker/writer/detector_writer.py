import logging

import numpy
import zmq

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
    pulse_id_step = 1

    context = zmq.Context()

    ram_buffer = RamBuffer(n_modules=n_modules,
                           n_slots=n_slots)

    detector_reader = DetectorReader(ram_buffer=ram_buffer,
                                     detector_folder=detector_folder,
                                     n_modules=n_modules,
                                     zmq_context=context)
    detector_reader.start_reading(start_pulse_id=start_pulse_id,
                                  end_pulse_id=end_pulse_id)

    image_assembler = ImageAssembler(ram_buffer=ram_buffer,
                                     n_modules=n_modules)

    detector_writer = DetectorWriter(output_file=output_file)

    for pulse_id in range(start_pulse_id, end_pulse_id, pulse_id_step):
        meta_buffer, data_buffer = image_assembler.get_data(pulse_id)
        detector_writer.write(pulse_id, meta_buffer, data_buffer)

    detector_writer.close()
    detector_reader.close()


class DetectorWriter(object):
    def __init__(self, output_file, n_images):
        self.output_file = output_file

        self.pulse_id_cache = numpy.zeros(shape=n_images, dtype="uint64")
        self.frame_index_cache = numpy.zeros(shape=n_images, dtype="uint64")
        self.daq_rec_cache = numpy.zeros(shape=n_images, dtype="uint32")
        self.is_good_frame_cache = numpy.zeros(shape=n_images, dtype="uint8")

    def write(self, pulse_id, meta_buffer, data_buffer):
        pass

    def close(self):
        pass
