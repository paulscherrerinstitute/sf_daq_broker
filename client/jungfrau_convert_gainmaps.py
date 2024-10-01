import argparse
import os
from datetime import datetime

import h5py
import numpy as np


DST_NAME = "gains"
GAINS = ("G0", "G1", "G2", "HG0", "HG1", "HG2")
MODULE_SHAPE = (6, 512, 1024)
MODULE_PIXELS = 512 * 1024


def main():
    parser = argparse.ArgumentParser(description="""
        Utility to read binary Jungfrau gain maps from PSI Detectors Group and save them in a 3d array in an hdf5 file.
        Gain maps are saved in a 3d array (with first index being G0, G1, G2), in the geometry specified by the optional argument --geometry. Some standard attributes are filled by default, like "date", "creator", "original_filenames".
        The name of the dataset used for saving the maps is "gains".
    """)

    parser.add_argument("files", metavar="file", nargs="+", help="Binary file as provided by the PSI Detector Group, usually one per module. Order matters! The first file provided is the bottom-left module.")
    parser.add_argument("--outfile", default="gains.h5", help="Name for the hdf5 output file")
    parser.add_argument("--attributes", nargs="+", default="", help="Additional attributes to be added to the destination dataset, in the form: key=value key=value ...")
    parser.add_argument("--shape", type=int, nargs=2, help="Dimension of the final image, in modules. For example, a 1.5 Jungfrau with three modules one on top of each other is: 3 1.")

    clargs = parser.parse_args()

    if clargs.shape is None:
        n_modules = len(clargs.files)
        clargs.shape = (n_modules, 1)

    modules = [np.fromfile(f, np.double) for f in clargs.files]

    for i, mod in enumerate(modules):
        if mod.ndim != 1:
            raise ValueError(f"module {i}: gain coefficients have unexpected shape {mod.shape}")
        shapex = mod.shape[0]
        if shapex == 3 * MODULE_PIXELS:
            print(f"module {i}: gain coefficients are only for G0, G1, G2. Expanding them to HG0, HG1, HG2 (copy: G0, G1, G2)")
            modules[i] = np.append(mod, mod[:3 * MODULE_PIXELS])
        elif shapex == 4 * MODULE_PIXELS:
            print(f"module {i}: gain coefficients are only for G0, G1, G2, HG0. Expanding them to HG1, HG2 (copy: G1, G2)")
            modules[i] = np.append(mod, mod[MODULE_PIXELS : 3 * MODULE_PIXELS])
        elif shapex == 6 * MODULE_PIXELS:
            print(f"module {i}: gain coefficients are complete G0, G1, G2, HG0, HG1, HG2.")
        else:
            raise ValueError(f"module {i}: gain coefficients have unexpected shape {shapex}")

    modules = [i.reshape(MODULE_SHAPE) for i in modules]

    res = merge_gainmaps(modules, clargs.shape, MODULE_SHAPE)

    with h5py.File(clargs.outfile, "w") as h5f:
        dst = h5f.create_dataset(DST_NAME, data=res)

        dst.attrs["creator"] = os.getenv("USER")
        dst.attrs["date"] = datetime.now().strftime("%Y%m%d %H:%M:%S")
        dst.attrs["original_filenames"] = " ".join(clargs.files)

        for kv in clargs.attributes:
            if kv == "":
                continue
            key, val = kv.split("=")
            dst.attrs[key] = val

        print()
        print(f"File {clargs.outfile} written, size of {DST_NAME} dataset: {dst.shape}")
        print("Written attributes:")
        for k, v in dst.attrs.items():
            print(f"\t{k}: {v}")
        print("Gain averages:")
        for i in range(MODULE_SHAPE[0]):
            gain = GAINS[i]
            avg = dst[i].mean()
            std = dst[i].std()
            print(f"\t{gain}: {avg:.2f} +- {std:.2f}")



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



