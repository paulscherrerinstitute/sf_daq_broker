import os

import numpy

from sf_daq_broker.detector.buffer_reader import FrameMetadata, META_FRAME_BYTES, FILE_MOD, BUFFER_FRAME_BYTES
from sf_daq_broker.detector.image_assembler import JF_N_PACKETS_PER_FRAME


def fill_test_meta_and_data(metadata, data, pulse_id, module_id):
    metadata.pulse_id = pulse_id
    metadata.module_id = module_id
    metadata.frame_index = pulse_id + 1000
    metadata.daq_rec = pulse_id + 10000
    metadata.n_recv_packets = JF_N_PACKETS_PER_FRAME

    data += module_id


def fill_ram_buffer(ram_buffer, pulse_id):
    for module_id in range(ram_buffer.n_modules):

        meta_buffer, image_buffer = ram_buffer.get_frame_buffers(module_id, pulse_id)

        metadata = FrameMetadata.from_buffer(meta_buffer)
        data = numpy.frombuffer(image_buffer, dtype="uint16")

        fill_test_meta_and_data(metadata, data, pulse_id, module_id)


def test_ram_buffer(self, ram_buffer, pulse_id):
    image_meta, image_buffer = ram_buffer.get_image_buffers(pulse_id)

    image = numpy.frombuffer(image_buffer, dtype="uint16").reshape(1024 * ram_buffer.n_modules, 512)

    for module_id in range(ram_buffer.n_modules):
        metadata = FrameMetadata.from_buffer(image_meta, module_id * META_FRAME_BYTES)
        self.assertEqual(pulse_id, metadata.pulse_id)
        self.assertEqual(module_id, metadata.module_id)
        self.assertEqual(pulse_id + 1000, metadata.frame_index)
        self.assertEqual(pulse_id + 10000, metadata.daq_rec)
        self.assertEqual(JF_N_PACKETS_PER_FRAME, metadata.n_recv_packets)

        start_offset = module_id * 1024
        end_offset = start_offset + 1024

        frame_data = image[start_offset:end_offset, :]
        # We test only first and last line. Improves speed and we can still test modules boundary.
        first_line = frame_data[0, :]
        last_line = frame_data[-1, :]

        self.assertTrue(all((x == module_id for x in first_line)))
        self.assertTrue(all((x == module_id for x in last_line)))


def fill_binary_file(filename, pulse_id, module_id):

    file_slot_n = pulse_id % FILE_MOD

    output_file = os.fdopen(os.open(filename, os.O_RDWR | os.O_CREAT), 'rb+')

    metadata = FrameMetadata()
    data = numpy.zeros(dtype="uint16", shape=(1024, 512))

    fill_test_meta_and_data(metadata, data, pulse_id, module_id)

    metadata_offset = BUFFER_FRAME_BYTES * file_slot_n
    output_file.seek(metadata_offset)
    output_file.write(metadata)

    data_offset = metadata_offset + META_FRAME_BYTES
    output_file.seek(data_offset)
    output_file.write(data)

    output_file.close()
