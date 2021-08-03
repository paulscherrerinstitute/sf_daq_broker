import json

import h5py
import numpy as np

import jungfrau_utils as ju

import sys
from sf_daq_broker.writer.postprocess_raw import postprocess_raw

import os

import logging

_logger = logging.getLogger("broker_writer")

def convert_file(file_in, file_out, json_run_file, detector_config_file):

    with open(detector_config_file, "r") as detector_file:
        data = json.load(detector_file)

        detector_name = data["detector_name"]
        gain_file     = data["gain_file"]
        pedestal_file = data["pedestal_file"]

    with open(json_run_file, "r") as run_file:
        data = json.load(run_file)
        detector_params = data["detectors"][detector_name]

        compression      = detector_params.get("compression", False)
        conversion       = detector_params.get("adc_to_energy", False)
        disabled_modules = detector_params.get("disabled_modules", [])
        if conversion:
            mask                 = detector_params.get("mask", True)
            double_pixels_action = detector_params.get("double_pixels_action", "mask")
            geometry             = detector_params.get("geometry", False)
            gap_pixels           = detector_params.get("gap_pixels", True)
            factor               = detector_params.get("factor", None)
        else:
            mask                 = False
            double_pixels_action = "keep"
            geometry             = False
            gap_pixels           = False
            factor               = None

    file_tmp = file_in
    if len(disabled_modules)>0:
        _logger.info(f"Will reduce data file, disabled_modules: {disabled_modules}")
        if conversion:
            file_tmp = file_out+".tmp"
        else:
            file_tmp = file_out
        postprocess_raw.postprocess_raw(file_in, file_tmp, compression=compression, disabled_modules=disabled_modules)

    if conversion:

        with ju.File(
            file_tmp,
            gain_file=gain_file,
            pedestal_file=pedestal_file,
            conversion=conversion,
            mask=mask,
            double_pixels=double_pixels_action,
            gap_pixels=gap_pixels,
            geometry=geometry,
            parallel=False,
        ) as juf:
            n_input_frames = len(juf["data"])
            good_frames = np.nonzero(juf["is_good_frame"])[0]
            n_output_frames = len(good_frames)

            juf.export(
                file_out,
                index=good_frames,
                roi=None,
                compression=compression,
                factor=factor,
                dtype=None,
                batch_size=35,
            )
        #os.remove(file_tmp)

    else:
        with h5py.File(file_tmp, "r") as juf:
            n_input_frames = len(juf[f"data/{detector_name}/data"])
            good_frames = np.nonzero(juf[f"data/{detector_name}/is_good_frame"])[0]
            n_output_frames = len(good_frames)

    # Utility info
    with h5py.File(file_out, "r") as h5f:
        _logger.info("daq_rec          : %s" % h5f[f"/data/{detector_name}/daq_rec"][0, 0])

        frame_index = h5f[f"/data/{detector_name}/frame_index"][:]
        _logger.info("frame_index range: (%d - %d)" % (np.min(frame_index), np.max(frame_index)))

    _logger.info(f"input frames : {n_input_frames}")
    _logger.info(f"bad frames   : {n_input_frames - n_output_frames}")
    _logger.info(f"output frames: {n_output_frames}")

    _logger.info(f"gain_file           : {gain_file}")
    _logger.info(f"pedestal_file       : {pedestal_file}")
    _logger.info(f"conversion          : {conversion}")
    _logger.info(f"mask                : {mask}")
    _logger.info(f"double_pixels_action: {double_pixels_action}")
    _logger.info(f"geometry            : {geometry}")
    _logger.info(f"gap_pixels          : {gap_pixels}")
    _logger.info(f"compression         : {compression}")
    _logger.info(f"factor              : {factor}")
