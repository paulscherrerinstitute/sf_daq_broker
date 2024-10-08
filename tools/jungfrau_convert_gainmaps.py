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
    dtnow = datetime.now()
    today = dtnow.strftime("%Y-%m-%d")
    output_default = f"gains_{today}.h5"

    parser = argparse.ArgumentParser(description=f'''
        Utility to read binary Jungfrau gain maps from the PSI Detector Group and write them as 3D array to a hdf5 file.
        The first axis in the 3D array is {PRINTABLE_GAINS}.
        The name of the dataset used for saving the maps is "{DST_NAME}".
        Some attributes are filled by default: "creator", "timestamp", "input_files".
    ''')

    parser.add_argument("fnames", metavar="file", nargs="+", help="Binary files as provided by the PSI Detector Group, usually one per module. Order matters! The first file provided is the bottom-left module.")
    parser.add_argument("-o", "--output", default=output_default, help=f"Name for the hdf5 output file (default: {output_default})")
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
    attributes["timestamp"] = dtnow.strftime("%Y-%m-%d %H:%M:%S")
    attributes["input_files"] = ", ".join(fnames)

    modules = [load_module(i, fn) for i, fn in enumerate(fnames)]
    data = merge_gainmaps(modules, shape, MODULE_SHAPE)

    write_file(fn_out, data, attributes)
    check_file(fn_out)



def load_module(index, fname):
    mod = np.fromfile(fname, np.double)

    msg = f"Module {index}: gain coefficients"

    if mod.ndim != 1:
        raise ValueError(f"{msg} have unexpected shape {mod.shape}")

    shapex = mod.shape[0]
    if shapex == 3 * MODULE_PIXELS:
        print(f"{msg} are only for G0, G1, G2 - expanding to HG0, HG1, HG2 by copying G0, G1, G2")
        mod = np.append(mod, mod[:3 * MODULE_PIXELS])
    elif shapex == 4 * MODULE_PIXELS:
        print(f"{msg} are only for G0, G1, G2, HG0 - expanding to HG1, HG2 by copying G1, G2")
        mod = np.append(mod, mod[MODULE_PIXELS : 3 * MODULE_PIXELS])
    elif shapex == 6 * MODULE_PIXELS:
        print(f"{msg} are complete G0, G1, G2, HG0, HG1, HG2")
    else:
        raise ValueError(f"{msg} have unexpected shape {shapex}")

    mod = mod.reshape(MODULE_SHAPE)
    return mod



def merge_gainmaps(modules, shape, module_shape):
    nheight, nwidth = shape
    msgain, msheight, mswidth = module_shape

    output_shape = (
        msgain,
        msheight * nheight,
        mswidth  * nwidth
    )

    output = np.zeros(output_shape, dtype=float)

    for h in range(nheight):
        for w in range(nwidth):
            for g in range(msgain):
                istart = msheight * h
                istop  = msheight * (h + 1)

                jstart = mswidth  * w
                jstop  = mswidth  * (w + 1)

                output[g, istart:istop, jstart:jstop] = modules[h + w][g]

    return output



def write_file(fn_out, data, attributes):
    with h5py.File(fn_out, "w") as h5f:
        dst = h5f.create_dataset(DST_NAME, data=data)
        dst.attrs.update(attributes)



def check_file(fn_out):
    with h5py.File(fn_out, "r") as h5f:
        dst = h5f["gains"]

        print()
        print(f'File "{fn_out}" written')
        print(f'Shape of "{DST_NAME}" dataset: {dst.shape}')

        print()
        print("Written attributes:")
        for k, v in dst.attrs.items():
            print(f"\t{k}: {v}")

        print()
        print("Gain averages:")
        for i, gain in enumerate(GAINS):
            vals = dst[i][:]
            avg = vals.mean()
            std = vals.std()
            print(f"\t{gain}:\t{avg:.2f}\t+/-\t{std:.2f}")

        print()





if __name__ == "__main__":
    main()



