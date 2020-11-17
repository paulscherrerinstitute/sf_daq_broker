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


N_RAM_BUFFER_SLOTS = 10


def write_detector_raw_from_detector_buffer(output_file, start_pulse_id, stop_pulse_id, pulse_id_step, metadata):

    detector_folder = "/tmp/det"
    n_modules = 16

    context = zmq.Context()

    ram_buffer = RamBuffer(n_modules=n_modules,
                           n_slots=N_RAM_BUFFER_SLOTS)

    detector_reader = DetectorReader(ram_buffer=ram_buffer,
                                     detector_folder=detector_folder,
                                     n_modules=n_modules,
                                     zmq_context=context)

    image_assembler = ImageAssembler(ram_buffer=ram_buffer,
                                     n_modules=n_modules,
                                     zmq_context=context)

    detector_writer = DetectorWriter(output_file=output_file)

    detector_reader.start_reading(start_pulse_id=start_pulse_id,
                                  stop_pulse_id=stop_pulse_id)

    for pulse_id in range(start_pulse_id, stop_pulse_id+1, pulse_id_step):
        meta_buffer, data_buffer = image_assembler.get_image(pulse_id)
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
