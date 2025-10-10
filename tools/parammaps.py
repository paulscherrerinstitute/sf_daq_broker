#!/usr/bin/env python

from collections import defaultdict

from sf_daq_broker.detector.detector_config import DETECTOR_PORT, DETECTOR_UDP_SRCIP#, DETECTOR_UDP_SRCMAC
from sf_daq_broker.utils import parse_det_name


def collect_data(d):
    vmin = min(d.values())
    vmax = max(d.values())

    res = defaultdict(list)
    res.update({i: [] for i in range(vmin, vmax + 1)})

    for name, port in d.items():
        num, ntiles, _ = parse_det_name(name)
        for i in range(ntiles):
            entry = f"{num}:{i}"
            res[port + i].append(entry)

    return res


def print_table(d):
    for k, v in d.items():
#        if not v:
#            continue
        v = ",\t".join(v)
        print(k, v, sep="\t")



dat = DETECTOR_PORT
dat = DETECTOR_UDP_SRCIP
#dat = DETECTOR_UDP_SRCMAC
print_table(collect_data(dat))



