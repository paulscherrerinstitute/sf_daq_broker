from ctypes import *

FOLDER_MOD = 100000
FILE_MOD = 1000
FILE_EXTENSION = ".bin"
# Module X * Y * 2 (16 bits)
MODULE_N_BYTES = 1024 * 512 * 2


class BufferBinaryFormat(Structure):
    _pack_ = 1
    _fields_ = [
        ("FORMAT_MARKER", c_char),
        ("pulse_id", c_uint64),
        ("frame_index", c_uint64),
        ("daq_rec", c_uint64),
        ("n_recv_packets", c_uint64),
        ("module_id", c_uint64),
        ("data", c_byte * MODULE_N_BYTES)
    ]


BUFFER_FRAME_BYTES = sizeof(BufferBinaryFormat)


class BufferReader(object):
    def __init__(self, ram_buffer, detector_folder, module_name):
        self.ram_buffer = ram_buffer
        self.detector_folder = detector_folder
        self.module_name = module_name

        self._file = None
        self._filename = None

    def get_frame(self, pulse_id):
        pulse_filename, pulse_index = self._get_pulse_id_location(pulse_id)

        if pulse_filename != self._filename:
            self._open_file(pulse_filename)

        n_bytes_offset = pulse_index * BUFFER_FRAME_BYTES

    def _get_pulse_id_location(self, pulse_id):
        data_folder = pulse_id // FOLDER_MOD
        data_folder *= FOLDER_MOD

        data_file = pulse_id // FILE_MOD
        data_file *= FILE_MOD

        filename = "%s/%s/%s/%s%s" % (self.detector_folder,
                                      self.module_name,
                                      data_folder,
                                      data_file,
                                      FILE_EXTENSION)

        # Index inside the data_file for the provided pulse_id.
        pulse_id_index = pulse_id - data_file

        return filename, pulse_id_index

    def _open_file(self, new_filename):

        if self._file:
            self._file.close()

        # buffering=0 turns buffering off
        self._file = open(new_filename, mode='rb', buffering=0)
        self._filename = new_filename
