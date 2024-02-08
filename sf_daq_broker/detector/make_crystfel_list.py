import logging

import h5py

from sf_daq_broker.utils import json_load


_logger = logging.getLogger("broker_writer")



def make_crystfel_list(data_file, run_info_file, detector):
    #TODO: why is this done? contents of run_info_file is not used...
    try:
        _parameters = json_load(run_info_file)
    except Exception as e:
        _logger.error(f"cannot read provided run info file {run_info_file} (due to: {e})")
        return

    try:
        f = h5py.File(data_file, "r")
    except Exception as e:
        _logger.error(f"cannot open provided data file {data_file} (due to: {e})")
        return

    pulseids = f[f"/data/{detector}/pulse_id"][:]
    n_pulse_id = len(pulseids)

    if f"/data/{detector}/is_good_frame" in f:
        is_good_frame = f[f"/data/{detector}/is_good_frame"][:]
    else:
        is_good_frame = [1] * n_pulse_id

    daq_recs = f[f"/data/{detector}/daq_rec"][:]

    nGoodFrames = 0
    nProcessedFrames = 0

    index_dark = []
    index_light = []

    for i in range(len(pulseids)):
        if not is_good_frame[i]:
            continue

        nGoodFrames += 1
#        p = pulseids[i]
        nProcessedFrames += 1
        daq_rec = daq_recs[i]

        event_laser    = bool((daq_rec>>16) & 1)
        event_darkshot = bool((daq_rec>>17) & 1)
#        event_fel      = bool((daq_rec>>18) & 1)
#        event_ppicker  = bool((daq_rec>>19) & 1)

        laser_on = False
        if not event_darkshot:
            laser_on = event_laser

        if laser_on:
            index_light.append(i)
        else:
            index_dark.append(i)

    f.close()

    n_total = len(pulseids)
    n_dark  = len(index_dark)
    n_light = len(index_light)

    _logger.info(f"total number of frames: {n_total}, number of good frames: {nGoodFrames}, number of processed frames: {nProcessedFrames}, number of output frames: {n_dark} (dark) {n_light} (light)")

    if index_dark:
        write_list_file(data_file, "dark", index_dark)

    if index_light:
        write_list_file(data_file, "light", index_light)



def write_list_file(fn_data, ptype, indices, delim="//"):
    basename = fn_data[:-3]
    fn = f"{basename}.{ptype}.lst"

    n_indices = len(indices)
    _logger.info(f"list of {n_indices} {ptype} frames: {fn}")

    with open(fn, "w") as f:
        for frame_number in indices:
            print(f"{fn_data} {delim}{frame_number}", file=f)



