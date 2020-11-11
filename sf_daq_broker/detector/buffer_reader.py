FOLDER_MOD = 100000
FILE_MOD = 1000
FILE_EXTENSION = ".bin"


class BufferReader(object):
    def __init__(self, ram_buffer, detector_folder, module_name):
        self.ram_buffer = ram_buffer
        self.detector_folder = detector_folder
        self.module_name = module_name

        self._file = None
        self._filename = None

    def get_frame(self, pulse_id):
        pulse_filename = self._get_filename_for_pulse_id(pulse_id)

        if pulse_filename != self._filename:
            self._open_file(pulse_filename)

    def _open_file(self, new_filename):

        if self._file:
            self._file.close()

        # buffering=0 turns buffering off
        self._file = open(new_filename, mode='rb', buffering=0)
        self._filename = new_filename

    def _get_filename_for_pulse_id(self, pulse_id):
        data_folder = pulse_id // FOLDER_MOD
        data_folder *= FOLDER_MOD

        data_file = pulse_id // FILE_MOD
        data_file *= FILE_MOD

        return "%s/%s/%s/%s%s" % (self.detector_folder,
                                  self.module_name,
                                  data_folder,
                                  data_file,
                                  FILE_EXTENSION)
