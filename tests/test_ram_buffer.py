import unittest

from sf_daq_broker.detector.buffer_reader import FrameMetadata, META_FRAME_BYTES
from sf_daq_broker.detector.image_assembler import JF_N_PACKETS_PER_FRAME
from sf_daq_broker.detector.ram_buffer import RamBuffer


class TestRamBuffer(unittest.TestCase):

    def test_enforce_min_buffer_size(self):
        with self.assertRaisesRegex(ValueError, "at least 5 slots"):
            RamBuffer(n_modules=1, n_slots=4)

    def test_store_and_load(self):
        n_modules = 3
        n_slots = 5
        pulse_ids = list(range(100, 105))

        ram_buffer = RamBuffer(n_modules=n_modules, n_slots=n_slots)

        for pulse_id in pulse_ids:
            for module_id in range(n_modules):
                meta_buffer, image_buffer = ram_buffer.get_frame_buffers(module_id, pulse_id)

                metadata = FrameMetadata.from_buffer(meta_buffer)
                metadata.pulse_id = pulse_id
                metadata.module_id = module_id
                metadata.frame_index = pulse_id + 1000
                metadata.daq_rec = pulse_id + 10000
                metadata.n_recv_packets = JF_N_PACKETS_PER_FRAME

        for pulse_id in pulse_ids:
            image_meta, image_buffer = ram_buffer.get_image_buffers(pulse_id)

            for module_id in range(n_modules):
                metadata = FrameMetadata.from_buffer(image_meta, module_id * META_FRAME_BYTES)
                self.assertEqual(pulse_id, metadata.pulse_id)
                self.assertEqual(module_id, metadata.module_id)
                self.assertEqual(pulse_id+1000, metadata.frame_index)
                self.assertEqual(pulse_id+10000, metadata.daq_rec)
                self.assertEqual(JF_N_PACKETS_PER_FRAME, metadata.n_recv_packets)

