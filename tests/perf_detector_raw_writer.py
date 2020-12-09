import numpy
import h5py
import numpy
import zmq
class DetectorRawWriter(object):
    def __init__(self, output_file, n_images, n_modules, metadata):
        self.output_file = output_file
        self.n_modules = n_modules
        self.metadata = metadata
        # TODO: Put real name here, please.
        self.detector_name = "detector"

        self.pulse_id_cache = numpy.zeros(shape=n_images, dtype="uint64")
        self.frame_index_cache = numpy.zeros(shape=n_images, dtype="uint64")
        self.daq_rec_cache = numpy.zeros(shape=n_images, dtype="uint32")
        self.is_good_frame_cache = numpy.zeros(shape=n_images, dtype="uint8")

        self.file = h5py.File(self.output_file, "w")

        self._create_metadata_datasets(metadata)

        self.current_write_index = 0

        self._image_dataset = self.file.create_dataset(
            name="/data/" + self.detector_name + "/data",
            dtype="uint16",
            shape=(n_images, self.n_modules * 512, 1024),
            chunks=(1, self.n_modules * 512, 1024)
        )

    def _create_metadata_datasets(self, metadata):

        for key, value in metadata.items():
            self.file.create_dataset(key, data=numpy.string_(value))

    def write(self, pulse_id, meta_buffer, data_buffer):
        self._image_dataset.id.write_direct_chunk((self.current_write_index, 0, 0),
                                                  data_buffer[:])

        self.pulse_id_cache[self.current_write_index] = meta_buffer["pulse_id"]
        self.frame_index_cache[self.current_write_index] = meta_buffer["frame_index"]
        self.daq_rec_cache[self.current_write_index] = meta_buffer["daq_rec"]
        self.is_good_frame_cache[self.current_write_index] = meta_buffer["is_good_image"]

        self.current_write_index += 1

    def _write_metadata(self):
        self.file["/data/" + self.detector_name + "/pulse_id"] = self.pulse_id_cache
        self.file["/data/" + self.detector_name + "/frame_index"] = self.frame_index_cache
        self.file["/data/" + self.detector_name + "/daq_rec"] = self.daq_rec_cache
        self.file["/data/" + self.detector_name + "/is_good_frame"] = self.is_good_frame_cache

    def close(self):
        self._write_metadata()
        self.file.close()


output_file = "/sf/alvra/data/p17502/raw/test_python_direct.h5"
n_images = 10000
n_modules = 4
metadata = {}

meta_buffer = {
    "pulse_id": 12345,
    "daq_rec": 12346,
    "frame_index": 12345,
    "is_good_image": True
}

source = numpy.zeros(dtype="uint16", shape=[512 * n_modules, 1024]) + 5
data_buffer = source.tobytes()

detector_writer = DetectorRawWriter(output_file=output_file, n_images=n_images, n_modules=n_modules, metadata=metadata)

for i in range(n_images):
    detector_writer.write(i, meta_buffer, data_buffer)

detector_writer.close()
