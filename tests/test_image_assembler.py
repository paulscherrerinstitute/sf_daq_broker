import struct
import unittest

import zmq

from sf_daq_broker.detector.buffer_reader import get_push_sender
from sf_daq_broker.detector.image_assembler import ImageAssembler
from sf_daq_broker.detector.ram_buffer import RamBuffer
from tests.utils import fill_ram_buffer


class TestImageAssembler(unittest.TestCase):
    def test_for_errors(self):

        context = zmq.Context()

        with self.assertRaisesRegex(ValueError, "The buffer must have at least 5 slots."):
            ImageAssembler(RamBuffer(n_modules=1, n_slots=4), n_modules=3, zmq_context=context)

        ram_buffer = RamBuffer(n_modules=3, n_slots=5)
        image_assembler = ImageAssembler(ram_buffer=ram_buffer, n_modules=3, zmq_context=context)
        senders = []

        with self.assertRaisesRegex(TimeoutError, "No data from buffer readers."):
            image_assembler.get_image(100)

        for i_module in range(3):
            sender = get_push_sender(context)
            sender.bind("inproc://%d" % i_module)
            senders.append(sender)

            sender.send(struct.pack("Q", 101))

        with self.assertRaisesRegex(ValueError, "Synchronization error"):
            image_assembler.get_image(102)

        # TODO: Test also image reconstruction missmatch
        #  (when modules are put together, pulse_id in metadata must match)

    def test_simple_assembly(self):
        n_modules = 3
        n_slots = 5

        pulse_ids = [100, 101, 102]
        senders = []

        context = zmq.Context()
        ram_buffer = RamBuffer(n_modules=n_modules, n_slots=n_slots)
        image_assembler = ImageAssembler(ram_buffer=ram_buffer, n_modules=n_modules, zmq_context=context)

        for pulse_id in pulse_ids:
            fill_ram_buffer(ram_buffer, pulse_id)

        for i_module in range(n_modules):
            sender = get_push_sender(context)
            sender.bind("inproc://%d" % i_module)
            senders.append(sender)

        for pulse_id in pulse_ids:
            for sender in senders:
                sender.send(struct.pack("Q", pulse_id))

            image_assembler.get_image(pulse_id)


