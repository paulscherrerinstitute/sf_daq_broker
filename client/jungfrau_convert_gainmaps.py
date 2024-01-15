import argparse
import os
from datetime import datetime

import h5py
import numpy as np

# a = np.fromfile("gainMaps_M022.bin", np.double)

GAINS = ["G0", "G1", "G2", "HG0", "HG1", "HG2"]

def merge_gainmaps(maps, shape, module_shape):
    if maps[0].shape != module_shape:
        print(f"[ERROR]: shape of the provided maps is not correct. Provided shape: {maps[0].shape}, required shape: {module_shape}")
    res = np.zeros([module_shape[0], shape[0] * module_shape[1], shape[1] * module_shape[2]], dtype=np.float)
    for i in range(shape[0]):
        for j in range(shape[1]):
            for z in range(module_shape[0]):
                ri = (i * module_shape[1], (i + 1) * module_shape[1])
                rj = (j * module_shape[2], (j + 1) * module_shape[2])
                res[z, ri[0]:ri[1], rj[0]:rj[1]] = maps[i + j][z]
    return res


def main():
    parser = argparse.ArgumentParser(description="""
Utility to read binary Jungfrau gain maps from PSI Detectors Group and save them in a 3d array in an hdf5 file.
    Gain maps are saved in a 3d array (with first index being G0, G1, G2), in the geometry specified by the optional argument --geometry. Some standard attributes are filled by default, like "date", "creator", "original_filenames".
    The name of the dataset used for saving the maps is "gains".

""")
    parser.add_argument("files", metavar="file", type=str,
                        help="Binary file as provided by the Detectors Group, usually one per module. Order matters! The first file provided is the bottom-left module.", nargs="+")
    parser.add_argument("--outfile", type=str, help="NAme for the hdf5 outputg", default="gains.h5")
    parser.add_argument("--attributes", type=str, help="Additional attributes to be added to the destination dataset, in the form key=value,key=value,...", default="")
    parser.add_argument("--shape", type=int, nargs=2, help="Dimension of the final image, in modules. For example, a 1.5 Jungfrau with three modules one on top of each other is [3,1].", default=[-1, -1])
    args = parser.parse_args()

    dst_name = "gains"
    module_shape = (6, 512, 1024)

    n_modules = len(args.files)
    if args.shape == [-1, -1]:
        args.shape = [n_modules, 1]

    maps = [np.fromfile(f, np.double) for f in args.files]

    for i in range(n_modules):
        if maps[i].shape[0] == 3 * 512 * 1024:
            print(f"{i}-module gain coefficients are only for G0,G1,G2. Expanding them to HG0,HG1,HG2 (copy G0,G1,G2)")
            maps[i] = np.append(maps[i], maps[i][:3 * 512 * 1024])
        if maps[i].shape[0] == 4 * 512 * 1024:
            print(f"{i}-module gain coefficients are only for G0,G1,G2,HG0. Expanding them to HG1,HG2 (copy G1,G2)")
            maps[i] = np.append(maps[i], maps[i][1024*512:3*1024*512])
            print(maps[i].shape[0])
    maps = [i.reshape(module_shape) for i in maps]

    res = merge_gainmaps(maps, args.shape, module_shape)

    f = h5py.File(args.outfile, "w")
    dst = f.create_dataset(dst_name, data=res)
    dst.attrs["creator"] = os.getenv("USER")
    dst.attrs["date"] = datetime.now().strftime("%Y%m%d %H:%M:%S")
    dst.attrs["original_filenames"] = " ".join(args.files)

    for kv in args.attributes.split(","):
        if kv == "":
            continue
        dst.attrs[kv.split("=")[0]] = kv.split("=")[1]

    print(f"File {args.outfile} written, size of {dst_name} dataset: {dst.shape}")
    print("Written attributes:")
    for k, v in dst.attrs.items():
        print(f"\t {k} = {v}")
    print("Gain averages:")
    for i in range(module_shape[0]):
        print(f"\t {GAINS[i]} = {dst[i].mean():.2f} +- {dst[i].std():.2f}")
    f.close()


if __name__ == "__main__":
    main()
