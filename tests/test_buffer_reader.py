import os
import unittest

from sf_daq_broker.detector.buffer_reader import ModuleReader
from sf_daq_broker.detector.ram_buffer import RamBuffer
from tests.utils import test_ram_buffer, fill_binary_file


class TestBufferReader(unittest.TestCase):

    needed_folder = "./M1/200000/"
    needed_file = "202000.bin"
    file_name = needed_folder + needed_file

    def setUp(self):
        os.makedirs("./M0/200000/", exist_ok=True)
        os.makedirs("./M1/200000/", exist_ok=True)

        fill_binary_file("./M0/200000/202000.bin", pulse_id=202002, module_id=0)
        fill_binary_file("./M1/200000/202000.bin", pulse_id=202002, module_id=1)

    def tearDown(self):
        os.remove("./M0/200000/202000.bin")
        os.remove("./M1/200000/202000.bin")

        os.removedirs("./M0/200000/")
        os.removedirs("./M1/200000/")

    def test_frame_loading(self):
        n_modules = 2
        n_slots = 5
        detector_folder = "."

        ram_buffer = RamBuffer(n_modules=n_modules, n_slots=n_slots)
        module_0_reader = ModuleReader(ram_buffer=ram_buffer, detector_folder=detector_folder, module_id=0)
        module_1_reader = ModuleReader(ram_buffer=ram_buffer, detector_folder=detector_folder, module_id=1)

        module_0_reader.load_frame_to_ram_buffer(202002)
        module_1_reader.load_frame_to_ram_buffer(202002)

        test_ram_buffer(self, ram_buffer, 202002)
