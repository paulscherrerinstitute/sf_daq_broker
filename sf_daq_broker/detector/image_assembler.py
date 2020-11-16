import zmq


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

        for receiver in self.receivers:
            received_pulse_id = receiver.recv()

            if received_pulse_id != pulse_id:
                raise ValueError("Synchronization error. received_pulse_id %s, expected pulse_id %s" %
                                 (received_pulse_id, pulse_id))

        frames_meta, image_buffer = self.ram_buffer.get_image_buffers()

        image_meta = {}
        for module_meta in frames_meta:
            pass

        return image_meta, image_buffer

    def close(self):
        for receiver in self.receivers:
            receiver.close()

        self.receivers.clear()

