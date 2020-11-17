import numpy

from sf_daq_broker.writer.detector_raw_writer import DetectorRawWriter

output_file = "/sf/alvra/data/p17502/raw/test_python.h5"
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
