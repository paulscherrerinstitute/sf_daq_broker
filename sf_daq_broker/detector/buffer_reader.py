import threading
from ctypes import *

import zmq

FOLDER_MOD = 100000
FILE_MOD = 1000
FILE_EXTENSION = ".bin"


class FrameMetadata(Structure):
    _pack_ = 1
    _fields_ = [
        ("FORMAT_MARKER", c_char),
        ("pulse_id", c_uint64),
        ("frame_index", c_uint64),
        ("daq_rec", c_uint64),
        ("n_recv_packets", c_uint64),
        ("module_id", c_uint64),
    ]


META_FRAME_BYTES = sizeof(FrameMetadata)
# Module X * Y * 2 (16 bits)
DATA_FRAME_BYTES = 1024 * 512 * 2
BUFFER_FRAME_BYTES = META_FRAME_BYTES + DATA_FRAME_BYTES


class ModuleReader(object):
    def __init__(self, ram_buffer, detector_folder, module_id):
        self.ram_buffer = ram_buffer
        self.detector_folder = detector_folder
        self.module_id = module_id

        self._file = None
        self._filename = None

    def __del__(self):
        self.close_file()

    def load_frame_to_ram_buffer(self, pulse_id):
        pulse_filename, pulse_index = self._get_pulse_id_location(pulse_id)

        if pulse_filename != self._filename:
            self._open_file(pulse_filename)

        meta_buffer, data_buffer = self.ram_buffer.get_frame_buffers(self.module_id, pulse_id)

        n_bytes_meta_offset = pulse_index * BUFFER_FRAME_BYTES
        self._file.seek(n_bytes_meta_offset)

        meta_bytes = self._file.readinto(meta_buffer)
        if meta_bytes != META_FRAME_BYTES:
            raise ValueError("Read frame %d, got %d meta bytes but expected %d bytes." %
                             (pulse_id, meta_bytes, META_FRAME_BYTES))

        n_bytes_data_offset = n_bytes_meta_offset + META_FRAME_BYTES
        self._file.seek(n_bytes_data_offset)

        data_bytes = self._file.readinto(data_buffer)
        if data_bytes != DATA_FRAME_BYTES:
            raise ValueError("Read frame %d, got %d data bytes but expected %d bytes." %
                             (pulse_id, data_bytes, DATA_FRAME_BYTES))

    def _get_pulse_id_location(self, pulse_id):
        folder_base = int((pulse_id // FOLDER_MOD) * FOLDER_MOD)
        file_base = int((pulse_id // FILE_MOD) * FILE_MOD)

        filename = "%s/M%s/%s/%s%s" % (self.detector_folder,
                                       self.module_id,
                                       folder_base,
                                       file_base,
                                       FILE_EXTENSION)

        # Index inside the data_file for the provided pulse_id.
        pulse_id_index = pulse_id - file_base

        return filename, pulse_id_index

    def _open_file(self, new_filename):
        self.close_file()

        # buffering=0 turns buffering off
        self._file = open(new_filename, mode='rb', buffering=0)
        self._filename = new_filename

    def close_file(self):
        if self._file:
            self._file.close()


class DetectorReader(object):
    def __init__(self, ram_buffer, detector_folder, n_modules, zmq_context):
        self.ram_buffer = ram_buffer
        self.detector_folder = detector_folder
        self.n_modules = n_modules
        self.zmq_context = zmq_context

        self.continue_reading_event = threading.Event()
        self.continue_reading_event.clear()

        self.threads = []

    def start_reading(self, start_pulse_id, end_pulse_id, pulse_id_step):
        self.continue_reading_event.set()

        for module_id in range(self.n_modules):
            t = threading.Thread(target=self.read_thread, kwargs={
                "start_pulse_id": start_pulse_id,
                "end_pulse_id": end_pulse_id,
                "pulse_id_step": pulse_id_step,
                "module_id": module_id
            })
            t.start()

            self.threads.append(t)

    def close(self):
        self.continue_reading_event.clear()

        for t in self.threads:
            t.join()

        self.threads.clear()

    def read_thread(self, start_pulse_id, end_pulse_id, pulse_id_step, module_id):
        reader = ModuleReader(self.ram_buffer, self.detector_folder, module_id)

        pulse_id_generator = iter(range(start_pulse_id, end_pulse_id, pulse_id_step))

        sender = get_push_sender(self.zmq_context)

        try:
            sender.bind("inproc://%s" % module_id)

            while self.continue_reading_event.is_set():
                pulse_id = next(pulse_id_generator, None)

                # Pulse_id == None when all pulse_ids have been read.
                if pulse_id is None:
                    break

                reader.load_frame_to_ram_buffer(pulse_id)
                sender.send(pulse_id)

        finally:
            sender.close()


def get_push_sender(context):
    # We use the PUSH mechanism to moderate disk throughput.
    sender = context.socket(zmq.PUSH)
    # No buffering on send side - receiver dictates reading speed.
    sender.setsockopt(zmq.SNDHWM, 1)
    # If in 1 second there was nobody to read the pulse_id we abort.
    sender.setsockopt(zmq.SNDTIMEO, 1000)
    # And we wait indefinitely to send the last pulse_id to the writer.
    sender.setsockopt(zmq.LINGER, 0)

    return sender
