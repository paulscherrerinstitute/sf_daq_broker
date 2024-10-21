#!/usr/bin/env python

from sf_daq_broker.detector.detector_config import DETECTOR_PORT, DETECTOR_UDP_SRCIP, DETECTOR_UDP_SRCMAC


def collect_data(d):
    vmin = min(d.values())
    vmax = max(d.values())

    res = {i: [] for i in range(vmin, vmax + 1)}

    for name, port in d.items():
        num = get_det_num(name)
        ntiles = get_ntiles(name)
        for i in range(ntiles):
            entry = f"{num}:{i}"
            res[port + i].append(entry)

    return res


def get_det_num(name):
    num = name[2:4]
    return int(num)

def get_ntiles(name):
    num = name[5:7]
    return int(num)

def print_table(d):
    for k, v in d.items():
        v = ",\t".join(v)
        print(k, v, sep="\t")



dat = DETECTOR_PORT
dat = DETECTOR_UDP_SRCIP
#dat = DETECTOR_UDP_SRCMAC
print_table(collect_data(dat))



