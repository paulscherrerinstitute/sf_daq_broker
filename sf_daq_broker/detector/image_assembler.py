import struct

import zmq
from zmq import Again

from sf_daq_broker.detector.buffer_reader import FrameMetadata, META_FRAME_BYTES


JF_N_PACKETS_PER_FRAME = 128


class ImageAssembler(object):
    def __init__(self, ram_buffer, n_modules, zmq_context):
        self.ram_buffer = ram_buffer
        self.n_modules = n_modules
        self.zmq_context = zmq_context

        self.receivers = []

        # All pulse_ids are buffered on the receiver except the following (source of -4):
        # 1 in the sender buffer + 1 in the sender loop + 1 in the receiver loop + 1 padding slot
        zmq_rcv_hwm = self.ram_buffer.n_slots - 4
        if zmq_rcv_hwm < 1:
            raise ValueError("RamBuffer must have at least 5 slots.")

        for module_id in range(self.n_modules):
            # We use the PUSH/PULL mechanism to moderate disk throughput.
            receiver = self.zmq_context.socket(zmq.PULL)
            # No buffering on send side - receiver dictates reading speed.
            receiver.setsockopt(zmq.RCVHWM, zmq_rcv_hwm)
            # If in 1 second nothing was received we have a problem in reading.
            receiver.setsockopt(zmq.RCVTIMEO, 1000)

            receiver.connect("inproc://%s" % module_id)

            self.receivers.append(receiver)

    def get_image(self, pulse_id):

        try:
            # Pull next pulse id from readers.
            for receiver in self.receivers:
                # Unpack always return a tuple, even for single elements.
                received_pulse_id = struct.unpack("Q", receiver.recv())[0]

            # There is no possibility to loose pulses (except in case of corruption of buffer)
            if received_pulse_id != pulse_id:
                raise ValueError("Synchronization error. received_pulse_id %s, expected pulse_id %s" %
                                 (received_pulse_id, pulse_id))
        except zmq.Again:
            raise TimeoutError("No data from buffer readers.")

        frames_meta, image_buffer = self.ram_buffer.get_image_buffers(pulse_id)

        frame_index = None
        daq_rec = None
        is_good_image = True

        is_pulse_init = False

        # Inspect all frames metadata and mark image as good.
        for i_module in range(self.n_modules):
            module_offset = META_FRAME_BYTES * i_module
            metadata = FrameMetadata.from_buffer(frames_meta, module_offset)

            # We use only complete frames for metadata.
            if metadata.n_recv_packets != JF_N_PACKETS_PER_FRAME:
                is_good_image = False
                continue

            if metadata.pulse_id != pulse_id:
                raise ValueError("RamBuffer error. Expected pulse_id %s, got %s." % (pulse_id, metadata.pulse_id))

            if not is_pulse_init:
                frame_index = metadata.frame_index
                daq_rec = metadata.daq_rec
                is_pulse_init = True

            if is_good_image:
                if frame_index != metadata.frame_index:
                    is_good_image = False

                if daq_rec != metadata.daq_rec:
                    is_good_image = False

        image_meta = {
            "pulse_id": pulse_id,
            "frame_index": frame_index,
            "daq_rec": daq_rec,
            "is_good_image": is_good_image
        }

        return image_meta, image_buffer

    def close(self):
        for receiver in self.receivers:
            receiver.close()

        self.receivers.clear()

