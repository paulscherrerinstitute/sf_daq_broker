import argparse
import os
from datetime import datetime

import h5py
import numpy as np


DST_NAME = "gains"
GAINS = ("G0", "G1", "G2", "HG0", "HG1", "HG2")
MODULE_SHAPE = (6, 512, 1024)
MODULE_PIXELS = 512 * 1024

PRINTABLE_GAINS = ", ".join(GAINS)


def main():
    parser = argparse.ArgumentParser(description=f'''
        Utility to read binary Jungfrau gain maps from the PSI Detector Group and write them as 3D array to a hdf5 file.
        The first axis in the 3D array is {PRINTABLE_GAINS}.
        The name of the dataset used for saving the maps is "{DST_NAME}".
        Some attributes are filled by default: "creator", "date", "original_filenames".
    ''')

    parser.add_argument("fnames", metavar="file", nargs="+", help="Binary files as provided by the PSI Detector Group, usually one per module. Order matters! The first file provided is the bottom-left module.")
    parser.add_argument("-o", "--output", default="gains.h5", help="Name for the hdf5 output file")
    parser.add_argument("-a", "--attributes", metavar="ATTRIBUTE", nargs="+", default="", help="Additional attributes to be added to the destination dataset, in the form: key=value")
    parser.add_argument("-s", "--shape", metavar=("HEIGHT", "WIDTH"), type=int, nargs=2, help="Dimensions of the final image, in number of modules. For example, a 1.5M Jungfrau with three modules one on top of each other is: 3 1. Defaults to stacking vertically, if nothing is provided.")

    clargs = parser.parse_args()

    fnames = clargs.fnames
    fn_out = clargs.output
    attributes = dict(kv.split("=") for kv in clargs.attributes)

    shape = clargs.shape
    if shape is None:
        n_modules = len(fnames)
        shape = (n_modules, 1)

    attributes["creator"] = os.getenv("USER")
    attributes["date"] = datetime.now().strftime("%Y%m%d %H:%M:%S")
    attributes["original_filenames"] = " ".join(fnames)

    modules = [load_module(i, fn) for i, fn in enumerate(fnames)]
    data = merge_gainmaps(modules, shape, MODULE_SHAPE)

    with h5py.File(fn_out, "w") as h5f:
        dst = h5f.create_dataset(DST_NAME, data=data)
        dst.attrs.update(attributes)

    with h5py.File(fn_out, "r") as h5f:
        dst = h5f["gains"]
        print()
        print(f"File {fn_out} written, size of {DST_NAME} dataset: {dst.shape}")
        print("Written attributes:")
        for k, v in dst.attrs.items():
            print(f"\t{k}: {v}")
        print("Gain averages:")
        for i in range(MODULE_SHAPE[0]):
            gain = GAINS[i]
            avg = dst[i].mean()
            std = dst[i].std()
            print(f"\t{gain}: {avg:.2f} +- {std:.2f}")
        print()



def load_module(index, fname):
    mod = np.fromfile(fname, np.double)

    msg = f"module {index}: gain coefficients"

    if mod.ndim != 1:
        raise ValueError(f"{msg} have unexpected shape {mod.shape}")

    shapex = mod.shape[0]
    if shapex == 3 * MODULE_PIXELS:
        print(f"{msg} are only for G0, G1, G2. Expanding them to HG0, HG1, HG2 (copy: G0, G1, G2)")
        mod = np.append(mod, mod[:3 * MODULE_PIXELS])
    elif shapex == 4 * MODULE_PIXELS:
        print(f"{msg} are only for G0, G1, G2, HG0. Expanding them to HG1, HG2 (copy: G1, G2)")
        mod = np.append(mod, mod[MODULE_PIXELS : 3 * MODULE_PIXELS])
    elif shapex == 6 * MODULE_PIXELS:
        print(f"{msg} are complete G0, G1, G2, HG0, HG1, HG2.")
    else:
        raise ValueError(f"{msg} have unexpected shape {shapex}")

    mod = mod.reshape(MODULE_SHAPE)
    return mod



def merge_gainmaps(maps, shape, module_shape):
    if maps[0].shape != module_shape:
        print(f"[ERROR]: shape of the provided maps is not correct. Provided shape: {maps[0].shape}, required shape: {module_shape}")
    res = np.zeros([module_shape[0], shape[0] * module_shape[1], shape[1] * module_shape[2]], dtype=float)
    for i in range(shape[0]):
        for j in range(shape[1]):
            for z in range(module_shape[0]):
                ri = (i * module_shape[1], (i + 1) * module_shape[1])
                rj = (j * module_shape[2], (j + 1) * module_shape[2])
                res[z, ri[0]:ri[1], rj[0]:rj[1]] = maps[i + j][z]
    return res





if __name__ == "__main__":
    main()



