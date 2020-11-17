from sf_daq_broker.detector.buffer_reader import BUFFER_FRAME_BYTES, META_FRAME_BYTES, DATA_FRAME_BYTES


class RamBuffer(object):
    def __init__(self, n_modules, n_slots):
        self.n_modules = n_modules
        self.n_slots = n_slots

        if n_slots < 5:
            raise ValueError("The buffer must have at least 5 slots.")

        self.raw_buffer = bytearray(self.n_modules * self.n_slots * BUFFER_FRAME_BYTES)

    def get_frame_buffers(self, module_id, pulse_id):
        # pulse_id index in RAM buffer
        buffer_index = pulse_id % self.n_slots
        # pulse_id index bytes offset in RAM buffer
        pulse_id_offset = buffer_index * self.n_modules * BUFFER_FRAME_BYTES

        # Pulse_id slot offset + module_id offset in meta buffer.
        meta_offset_start = pulse_id_offset + (module_id * META_FRAME_BYTES)
        meta_offset_end = meta_offset_start + META_FRAME_BYTES

        # Pulse_id slot offset + metadata buffer offset + module_id offset in data buffer.
        data_offset_start = pulse_id_offset + (self.n_modules * META_FRAME_BYTES) + (module_id * DATA_FRAME_BYTES)
        data_offset_end = data_offset_start + DATA_FRAME_BYTES

        meta_buffer = memoryview(self.raw_buffer)[meta_offset_start:meta_offset_end]
        data_buffer = memoryview(self.raw_buffer)[data_offset_start:data_offset_end]

        return meta_buffer, data_buffer

    def get_image_buffers(self, pulse_id):
        # pulse_id index in RAM buffer
        buffer_index = pulse_id % self.n_slots
        # pulse_id index bytes offset in RAM buffer
        pulse_id_offset = buffer_index * self.n_modules * BUFFER_FRAME_BYTES

        # Pulse_id slot.
        meta_offset_start = pulse_id_offset
        meta_offset_end = meta_offset_start + META_FRAME_BYTES * self.n_modules

        # Pulse_id slot offset + data buffer offset
        data_offset_start = pulse_id_offset + META_FRAME_BYTES * self.n_modules
        data_offset_end = data_offset_start + DATA_FRAME_BYTES * self.n_modules

        meta_buffer = memoryview(self.raw_buffer)[meta_offset_start:meta_offset_end]
        data_buffer = memoryview(self.raw_buffer)[data_offset_start:data_offset_end]

        return meta_buffer, data_buffer
