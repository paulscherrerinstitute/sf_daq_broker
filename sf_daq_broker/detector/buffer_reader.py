
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

    def _get_filename_for_pulse_id(self):
        pass

