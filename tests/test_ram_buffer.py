import unittest
from sf_daq_broker.detector.ram_buffer import RamBuffer
from tests.utils import fill_ram_buffer, test_ram_buffer


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
            fill_ram_buffer(ram_buffer, pulse_id)

        for pulse_id in pulse_ids:
            test_ram_buffer(self, ram_buffer, pulse_id)

