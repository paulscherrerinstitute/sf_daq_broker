import argparse
import os
from collections import defaultdict

from sf_daq_broker.detector.detector_config import DetectorConfig, DETECTOR_NAMES
from sf_daq_broker.utils import json_load, json_save


BUFFER = "/gpfs/photonics/swissfel/buffer"
FN_CFG_TEMPL = f"{BUFFER}/config/{{detector_name}}.json"

#TODO: look up gain and pedestal files
EXTRA_PARAMS = {
    "gain_file": "",
    "pedestal_file": "",
    "live_rate": 100,
    "streamvis_rate": 100
}



class Choices(tuple):
    # adapted from https://github.com/python/cpython/issues/53834#issuecomment-1093515812

    def __init__(self, _iterable=None, default=None):
        # _iterable is already handled by tuple.__new__
        self.default = default or []

    def __contains__(self, item):
        return super().__contains__(item) or item == self.default


DETECTORS = Choices(sorted(DETECTOR_NAMES.keys()))



def run():
    dbcfs = "detector buffer config files"
    parser = argparse.ArgumentParser(description=f"create, update or compare {dbcfs}")

    subparsers = parser.add_subparsers(title="commands", required=True)

    parser_detname = argparse.ArgumentParser(add_help=False)
    parser_detname.add_argument("detectors", nargs="*", choices=DETECTORS, help="name(s) of (a) JF detector(s)")
    parser_detname.add_argument("--all", action="store_true", help="if no detectors are given, all detectors are used")

    commands = ["create", "update", "compare"]
    for cmd in commands:
        func = globals()[f"cmd_{cmd}"]
        parser_cmd = subparsers.add_parser(cmd, parents=[parser_detname], description=f"{cmd} {dbcfs}")
        parser_cmd.set_defaults(func=func)

    clargs = parser.parse_args()

    detectors = clargs.detectors

    if clargs.all:
        if detectors:
            raise SystemExit("ambiguous arguments: both detectors and --all set")
        detectors = DETECTORS
    elif not detectors:
        raise SystemExit("nothing to do")

    for dn in detectors:
        try:
            clargs.func(dn)
        except Exception as e:
            print(f"{e} -- skipping {dn}")


def cmd_create(detector_name):
    params = get_detector_params(detector_name)

    # the buffer expects a few extra params that are not part of DetectorConfig
    res = EXTRA_PARAMS.copy()
    res.update(params)

    fn_cfg = mk_fn_cfg(detector_name)
    json_save(res, fn_cfg, mode="x")


def cmd_update(detector_name):
    params_code = get_detector_params(detector_name)

    fn_cfg = mk_fn_cfg(detector_name)
    params_file = load_config_file(fn_cfg)

    params_file.update(params_code)

    json_save(params_file, fn_cfg)


def cmd_compare(detector_name):
    params_code = get_detector_params(detector_name)

    fn_cfg = mk_fn_cfg(detector_name)
    params_file = load_config_file(fn_cfg)

    diff = diff_dicts(params_code, params_file)
    print_table(detector_name, diff)



def get_detector_params(detector_name):
    try:
        cfg = DetectorConfig(detector_name)
    except RuntimeError as e:
        raise RuntimeError(f"cannot configure detector {detector_name} ({e})") from e

    params = {
        "detector_name":    cfg.get_detector_name(),
        "n_modules":        cfg.get_number_modules(),
        "streamvis_stream": cfg.get_detector_daq_public_address(),
        "live_stream":      cfg.get_detector_daq_data_address(),
        "start_udp_port":   cfg.get_detector_port_first_module(),
        "buffer_folder":    f"{BUFFER}/{detector_name}"
    }
    return params


def mk_fn_cfg(detector_name):
    return FN_CFG_TEMPL.format(detector_name=detector_name)


def load_config_file(fn_cfg):
    if not os.path.exists(fn_cfg):
        raise RuntimeError(f"buffer config file {fn_cfg} does not exist")
    return json_load(fn_cfg)


def diff_dicts(d1, d2):
    all_keys = d1.keys() | d2.keys()

    dd1 = defaultdict(Missing, d1)
    dd2 = defaultdict(Missing, d2)

    diff = {}
    for k in all_keys:
        v1 = dd1[k]
        v2 = dd2[k]
        if v1 != v2:
            diff[k] = (v1, v2)

    return diff


class Missing:
    """
    Semaphore for missing entries
    """

    def __repr__(self):
        return "<MISSING>"


def print_table(header, diff):
    #TODO: this is a bit ugly
    col1 = []
    col2 = []
    col3 = []
    for k, (v1, v2) in sorted(diff.items()):
        col1.append(k + ":")
        col2.append(repr(v1))
        col3.append(repr(v2))

    col1 = ljust(col1)
    col2 = rjust(col2)
    col3 = rjust(col3)

    header = header + ":"
    print(header)
    print("-" * len(header))

    #TODO
    if not col1:
        print("empty")

    for i1, i2, i3 in zip(col1, col2, col3):
        print(i1, i2, i3, sep=2 * " ")

    print()


def ljust(seq):
    length = maxstrlen(seq)
    return (str(i).ljust(length) for i in seq)

def rjust(seq):
    length = maxstrlen(seq)
    return (str(i).rjust(length) for i in seq)

def maxstrlen(seq):
    if not seq:
        return 0
    return max(len(str(i)) for i in seq)





if __name__ == "__main__":
    run()



