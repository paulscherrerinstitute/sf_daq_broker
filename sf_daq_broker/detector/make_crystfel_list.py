import json
import logging
import os
from time import sleep

import h5py
import numpy as np

_logger = logging.getLogger("broker_writer")

def make_crystfel_list(data_file, run_info_file, detector):

    try:
        with open(run_info_file) as json_file:
            parameters = json.load(json_file)
    except:
        _logger.error(f"Cannot read provided run file {run_info_file}, may be not json?")
        return

    try:
        f=h5py.File(data_file, "r")
    except:
        _logger.error(f"Cannot open {data_file}")
        return

    pulseids = f[f"/data/{detector}/pulse_id"][:]
    n_pulse_id = len(pulseids)
    if f"/data/{detector}/is_good_frame" in f.keys():
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
        p = pulseids[i]
        nProcessedFrames += 1
        daq_rec = daq_recs[i]
        event_laser    = bool((daq_rec>>16)&1)
        event_darkshot = bool((daq_rec>>17)&1)
        event_fel      = bool((daq_rec>>18)&1)
        event_ppicker  = bool((daq_rec>>19)&1)

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

    if len(index_dark) > 0:
        file_dark = data_file[:-3] + ".dark.lst"
        _logger.info(f"List of dark frames : {file_dark} , {len(index_dark)} frames")
        f_list = open(file_dark, "w")
        for frame_number in index_dark:
            print(f"{data_file} //{frame_number}", file = f_list)
        f_list.close()

    if len(index_light) > 0:
        file_light = data_file[:-3] + ".light.lst"
        _logger.info(f"List of light frames : {file_light} , {len(index_light)} frames")
        f_list = open(file_light, "w")
        for frame_number in index_light:
            print(f"{data_file} {delim}{frame_number}", file = f_list)
        f_list.close()

def store_dap_info(beamline=None, pgroup=None, detector=None, start_pulse_id=None, stop_pulse_id=None, file_name_out=None):

    if beamline is None or pgroup is None or detector is None or start_pulse_id is None or stop_pulse_id is None or file_name_out is None:
        _logger.error(f"input parameters to store_dap_info is not complete {beamline} {pgroup} {detector} {start_pulse_id} {stop_pulse_id} {file_name_out}")
        return

#    path_to_dap_files = f"/sf/{beamline}/data/{pgroup}/res/jungfrau/output/"
    path_to_dap_files = f"/gpfs/photonics/swissfel/buffer/dap/data/{detector}"
    if not os.path.exists(path_to_dap_files):
        _logger.error(f"dap output is not reachable, may be dap is not working, path: {path_to_dap_files}")
        return

    dap_ending = set([p//10000*10000 for p in range(start_pulse_id, stop_pulse_id+1)])


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
                    if pulse_id >= start_pulse_id and pulse_id <= stop_pulse_id:
                        print(line, file=file_out)
                        n_lines_out += 1

    _logger.info(f"{n_lines_out} lines of dap output is stored in file {file_name_out}")
