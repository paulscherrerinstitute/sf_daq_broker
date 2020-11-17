import logging
from time import time

import h5py
import numpy
import zmq

from sf_daq_broker.detector.buffer_reader import DetectorReader
from sf_daq_broker.detector.image_assembler import ImageAssembler
from sf_daq_broker.detector.ram_buffer import RamBuffer

_logger = logging.getLogger("broker_writer")

N_RAM_BUFFER_SLOTS = 10


def write_detector_raw_from_buffer(
        output_file, start_pulse_id, stop_pulse_id, pulse_id_step, metadata, detector_folder, n_modules):
    _logger.info("Writing %s from start_pulse_id %s to stop_pulse_id %s with pulse_id_step %s from folder %s."
                 % (output_file, start_pulse_id, stop_pulse_id, pulse_id_step, detector_folder))
    _logger.debug("n_modules %s" % n_modules)

    start_time = time()

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

    n_images = len(range(start_pulse_id, stop_pulse_id + 1, pulse_id_step))
    detector_writer = DetectorWriter(output_file=output_file, n_images=n_images, n_modules=n_modules, metadata=metadata)

    detector_reader.start_reading(start_pulse_id=start_pulse_id,
                                  stop_pulse_id=stop_pulse_id,
                                  pulse_id_step=pulse_id_step)

    for pulse_id in range(start_pulse_id, stop_pulse_id + 1, pulse_id_step):
        meta_buffer, data_buffer = image_assembler.get_image(pulse_id)
        detector_writer.write(pulse_id, meta_buffer, data_buffer)

    detector_writer.close()
    detector_reader.close()

    _logger.info("Data writing took %s seconds." % (time() - start_time))


class DetectorWriter(object):
    def __init__(self, output_file, n_images, n_modules, metadata):
        self.output_file = output_file
        self.n_modules = n_modules
        self.metadata = metadata
        # TODO: Put real name here, please.
        self.detector_name = "detector"

        self.pulse_id_cache = numpy.zeros(shape=n_images, dtype="uint64")
        self.frame_index_cache = numpy.zeros(shape=n_images, dtype="uint64")
        self.daq_rec_cache = numpy.zeros(shape=n_images, dtype="uint32")
        self.is_good_frame_cache = numpy.zeros(shape=n_images, dtype="uint8")

        self.file = h5py.File(self.output_file, "w")
        _logger.info("File %s created." % self.output_file)

        self._create_metadata_datasets(metadata)

        self.current_write_index = 0

        self._image_dataset = self.file.create_dataset(
            name="/data/" + self.detector_name + "/data",
            dtype="uint16",
            shape=(n_images, self.n_modules * 512, 1024),
            chunks=(1, self.n_modules * 512, 1024)
        )

    def __del__(self):
        self.close()

    def _create_metadata_datasets(self, metadata):
        _logger.debug("Initializing metadata datasets.")

        for key, value in metadata.items():
            self.file.create_dataset(key, data=numpy.string_(value))

    def write(self, pulse_id, meta_buffer, data_buffer):
        self._image_dataset.id.write_direct_chunk((self.current_write_index, 0, 0),
                                                  data_buffer)

        self.pulse_id_cache[self.current_write_index] = meta_buffer["pulse_id"]
        self.frame_index_cache[self.current_write_index] = meta_buffer["frame_index"]
        self.daq_rec_cache[self.current_write_index] = meta_buffer["daq_rec"]
        self.is_good_frame_cache[self.current_write_index] = meta_buffer["is_good_frame"]

    def _write_metadata(self):
        self.file["/data/" + self.detector_name + "/pulse_id"] = self.pulse_id_cache
        self.file["/data/" + self.detector_name + "/frame_index"] = self.frame_index_cache
        self.file["/data/" + self.detector_name + "/daq_rec"] = self.daq_rec_cache
        self.file["/data/" + self.detector_name + "/is_good_frame"] = self.is_good_frame_cache

    def close(self):
        self._write_metadata()
        self.file.close()
