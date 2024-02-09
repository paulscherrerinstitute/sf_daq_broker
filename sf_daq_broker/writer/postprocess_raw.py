import os
import struct

import bitshuffle
import h5py
import numpy as np
from bitshuffle.h5 import H5_COMPRESS_LZ4, H5FILTER  # pylint: disable=no-name-in-module


# bitshuffle hdf5 filter params
BLOCK_SIZE = 2048
COMPARGS = {
    "compression": H5FILTER,
    "compression_opts": (BLOCK_SIZE, H5_COMPRESS_LZ4)
}

# limit bitshuffle omp to a single thread
# a better fix would be to use bitshuffle compiled without omp support
os.environ["OMP_NUM_THREADS"] = "1"

DTYPE = np.dtype(np.uint16)
DTYPE_SIZE = DTYPE.itemsize

MODULE_SIZE_X = 1024
MODULE_SIZE_Y = 512



def postprocess_raw(source, dest, disabled_modules=(), index=None, compression=False, batch_size=100):
    with h5py.File(source, "r") as h5_source, h5py.File(dest, "w") as h5_dest:
        detector_name = h5_source["general/detector_name"][()].decode()
        dset_name = f"data/{detector_name}/data"

        # traverse the source file and copy/index all datasets, except the raw image data
        iv = ItemVisitor(h5_source, h5_dest, index, dset_name)
        h5_source.visititems(iv.visititems)

        # prepare dataset for raw image data
        dset = h5_source[dset_name]

        if index is None:
            n_images = dset.shape[0]
        else:
            index = np.array(index)
            n_images = len(index)

        n_modules = dset.shape[1] // MODULE_SIZE_Y
        n_disabled_modules = len(disabled_modules)
        n_enabled_modules = n_modules - n_disabled_modules
        out_shape = (MODULE_SIZE_Y * n_enabled_modules, MODULE_SIZE_X)

        args = {
            "shape"    : (n_images, *out_shape),
            "maxshape" : (n_images, *out_shape),
            "chunks"   : (1,        *out_shape)
        }

        if compression:
            args.update(COMPARGS)

        h5_dest.create_dataset_like(dset_name, dset, **args)

        # calculate and save module map
        module_map = []
        counter = 0
        for ind in range(n_modules):
            if ind in disabled_modules:
                entry = -1
            else:
                entry = counter
                counter += 1
            module_map.append(entry)

        h5_dest[f"data/{detector_name}/module_map"] = np.tile(module_map, (n_images, 1))

        # prepare buffers to be reused for every batch of images
        read_buffer = np.empty((batch_size, *dset.shape[1:]), dtype=DTYPE)
        out_buffer  = np.zeros((batch_size, *out_shape),      dtype=DTYPE)

        # process and write raw image data in batches
        for batch_start_ind in range(0, n_images, batch_size):
            batch_stop_ind = min(batch_start_ind + batch_size, n_images)
            batch_range = range(batch_start_ind, batch_stop_ind)

            if index is None:
                batch_ind = np.array(batch_range)
            else:
                batch_ind = index[batch_range]

            #TODO: avoid unnecessary buffers
            read_buffer_view = read_buffer[: len(batch_ind)]
            out_buffer_view  = out_buffer[: len(batch_ind)]

            # Avoid a stride-bottleneck: https://github.com/h5py/h5py/issues/977
            if np.sum(np.diff(batch_ind)) == len(batch_ind) - 1:
                # consecutive index values
                sel = np.s_[batch_ind]
                dset.read_direct(read_buffer_view, source_sel=sel)
            else:
                for i, j in enumerate(batch_ind):
                    sel_i = np.s_[i]
                    sel_j = np.s_[j]
                    dset.read_direct(read_buffer_view, source_sel=sel_j, dest_sel=sel_i)

            for i, m in enumerate(module_map):
                if m == -1:
                    continue

                istart = i * MODULE_SIZE_Y
                mstart = m * MODULE_SIZE_Y

                istop = (i + 1) * MODULE_SIZE_Y
                mstop = (m + 1) * MODULE_SIZE_Y

                read_slice = read_buffer_view[:, istart:istop, :]
                out_slice = out_buffer_view[:, mstart:mstop, :]
                out_slice[:] = read_slice

            bytes_num_elem = struct.pack(">q", out_shape[0] * out_shape[1] * DTYPE_SIZE)
            bytes_block_size = struct.pack(">i", BLOCK_SIZE * DTYPE_SIZE)
            header = bytes_num_elem + bytes_block_size

            for pos, im in zip(batch_range, out_buffer_view):
                if compression:
                    byte_array = header + bitshuffle.compress_lz4(im, BLOCK_SIZE).tobytes()
                else:
                    byte_array = im.tobytes()

                h5_dest[dset_name].id.write_direct_chunk((pos, 0, 0), byte_array)



class ItemVisitor:

    def __init__(self, h5_source, h5_dest, indices, skip):
        self.h5_source = h5_source
        self.h5_dest = h5_dest
        self.indices = indices
        self.skip = skip


    def visititems(self, name, obj):
        if name == self.skip:
            return

        h5_source = self.h5_source
        h5_dest = self.h5_dest
        indices = self.indices

        if isinstance(obj, h5py.Group):
            h5_dest.create_group(name)

        elif isinstance(obj, h5py.Dataset):
            dset_source = h5_source[name]

            # datasets with BS data, so indexing along pulse ID axis should be applied
            if name.startswith("data"):
                if indices is None:
                    data = dset_source[:]
                else:
                    data = dset_source[indices, :]

                h5_dest.create_dataset_like(name, dset_source, data=data, shape=data.shape)

            # datasets with non-BS data
            else:
                h5_dest.create_dataset_like(name, dset_source, data=dset_source)

        else:
            raise TypeError(f"unknown h5py object type: {name} ({obj})")

        # copy group/dataset attributes
        for key, value in h5_source[name].attrs.items():
            h5_dest[name].attrs[key] = value



