import logging
import os
from time import sleep

import h5py

from sf_daq_broker.utils import json_load


_logger = logging.getLogger("broker_writer")



def make_crystfel_list(data_file, run_info_file, detector):
    try:
        _parameters = json_load(run_info_file)
    except Exception as e:
        _logger.error(f"Cannot read provided run file {run_info_file}, may be not json? (due to {e})")
        return

    try:
        f = h5py.File(data_file, "r")
    except Exception as e:
        _logger.error(f"Cannot open {data_file} (due to {e})")
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

    _logger.info(f"Total number of frames: {len(pulseids)}, number of good frames : {nGoodFrames}, processed frames: {nProcessedFrames}, outputed frames: {len(index_dark)}(dark) {len(index_light)}(light)")

    delim = "//"

    if index_dark:
        file_dark = data_file[:-3] + ".dark.lst"
        _logger.info(f"List of dark frames : {file_dark} , {len(index_dark)} frames")
        with open(file_dark, "w") as f_list:
            for frame_number in index_dark:
                print(f"{data_file} {delim}{frame_number}", file = f_list)

    if index_light:
        file_light = data_file[:-3] + ".light.lst"
        _logger.info(f"List of light frames : {file_light} , {len(index_light)} frames")
        with open(file_light, "w") as f_list:
            for frame_number in index_light:
                print(f"{data_file} {delim}{frame_number}", file = f_list)


def store_dap_info(beamline=None, pgroup=None, detector=None, start_pulse_id=None, stop_pulse_id=None, file_name_out=None):
    if None in (beamline, pgroup, detector, start_pulse_id, stop_pulse_id, file_name_out):
        _logger.error(f"input parameters to store_dap_info is not complete {beamline} {pgroup} {detector} {start_pulse_id} {stop_pulse_id} {file_name_out}")
        return

#    path_to_dap_files = f"/sf/{beamline}/data/{pgroup}/res/jungfrau/output/"
    path_to_dap_files = f"/gpfs/photonics/swissfel/buffer/dap/data/{detector}"
    if not os.path.exists(path_to_dap_files):
        _logger.error(f"dap output is not reachable, may be dap is not working, path: {path_to_dap_files}")
        return

    dap_ending = set(p // 10000 * 10000 for p in range(start_pulse_id, stop_pulse_id + 1))

    sleep(10)

    n_lines_out = 0

    with open(file_name_out, "w") as file_out:
        for dap_f_ending in dap_ending:
#            dap_file_name = f"{path_to_dap_files}/{dap_f_ending}.{detector}.dap"
            dap_file_name = f"{path_to_dap_files}/{dap_f_ending}.dap"
            if not os.path.exists(dap_file_name):
                continue
            with open(dap_file_name, "r") as dap_file:
                all_lines = dap_file.read().splitlines()
                for line in all_lines:
                    pulse_id = int(line.split()[0])
                    if start_pulse_id <= pulse_id <= stop_pulse_id:
                        print(line, file=file_out)
                        n_lines_out += 1

    _logger.info(f"{n_lines_out} lines of dap output is stored in file {file_name_out}")



