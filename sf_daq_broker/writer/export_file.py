import logging
import os

import h5py
import jungfrau_utils as ju
import numpy as np

from sf_daq_broker.utils import json_load


_logger = logging.getLogger("broker_writer")



def convert_file(file_in, file_out, json_run_file, detector_config_file):
    data = json_load(detector_config_file)

    detector_name = data["detector_name"]
    gain_file     = data["gain_file"]
    pedestal_file = data["pedestal_file"]


    data = json_load(json_run_file)

    detector_params = data["detectors"][detector_name]

    compression      = detector_params.get("compression", False)
    conversion       = detector_params.get("adc_to_energy", False)
    disabled_modules = detector_params.get("disabled_modules", [])
    remove_raw_files = detector_params.get("remove_raw_files", False)
    downsample       = detector_params.get("downsample", None)

    if downsample is not None:
        if isinstance(downsample, list):
            downsample = tuple(downsample)
        if not (isinstance(downsample, tuple) and len(downsample) == 2 and isinstance(downsample[0], int) and isinstance(downsample[1], int)):
            _logger.error(f"Bad option for the downsample parameter : {downsample}. Ignoring it.")
            downsample = None

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

    selected_pulse_ids = data.get("selected_pulse_ids", [])
    save_ppicker_events_only = detector_params.get("save_ppicker_events_only", False)
    roi = detector_params.get("roi", None)


    files_to_remove = set()

    if conversion or len(disabled_modules) > 0 or len(selected_pulse_ids) > 0 or save_ppicker_events_only:
        files_to_remove.add(file_in)

        with ju.File(
            file_in,
            gain_file=gain_file,
            pedestal_file=pedestal_file,
            conversion=conversion,
            mask=mask,
            double_pixels=double_pixels_action,
            gap_pixels=gap_pixels,
            geometry=geometry,
            parallel=True,
        ) as juf:
            n_input_frames = len(juf["data"])
            if len(selected_pulse_ids) == 0:
                good_frames = np.nonzero(juf["is_good_frame"])[0]
            else:
                good_frames = []
                is_good_frames = juf["is_good_frame"]
                det_pulse_ids = juf["pulse_id"]
                for pulse_index in range(n_input_frames):
                    if is_good_frames[pulse_index] != 0 and det_pulse_ids[pulse_index][0] in selected_pulse_ids:
                        good_frames.append(pulse_index)


            if save_ppicker_events_only:
                good_frames_filtered = []
                daq_recs = juf["daq_rec"]
                for pulse_index in good_frames:
                    daq_rec = daq_recs[pulse_index][0]
#                    event_fel      = bool((daq_rec>>18)&1)
                    event_ppicker  = bool((daq_rec>>19)&1)
#                    if event_fel and event_ppicker:
                    if event_ppicker:
                        good_frames_filtered.append(pulse_index)

                if not np.array_equal(good_frames, good_frames_filtered):
                    excluded_indexes = list(set(good_frames)-set(good_frames_filtered))
                    _logger.info(f"Some frames ({len(excluded_indexes)}) were dropped because of requirement on ppicker")
                    good_frames = good_frames_filtered
                else:
                    _logger.info("No frames were dropped because of requirement on ppicker")


            n_output_frames = len(good_frames)

            if n_output_frames:
                juf.export(
                    file_out,
                    disabled_modules=disabled_modules,
                    index=good_frames,
                    roi=roi,
                    downsample=downsample,
                    compression=compression,
                    factor=factor,
                    dtype=None,
                    batch_size=35,
                )
            else:
                _logger.info("No output frames selected, no jungfrau file produced. Will keep raw_data file")
                remove_raw_files = False

    else:
        with h5py.File(file_in, "r") as juf:
            n_input_frames = len(juf[f"data/{detector_name}/data"])
            good_frames = np.nonzero(juf[f"data/{detector_name}/is_good_frame"])[0]
            n_output_frames = len(good_frames)


    # Utility info
    _logger.info(f"input frames         : {n_input_frames}")
    _logger.info(f"skipped frames       : {n_input_frames - n_output_frames}")
    _logger.info(f"output frames        : {n_output_frames}")

    _logger.info(f"gain_file            : {gain_file}")
    _logger.info(f"pedestal_file        : {pedestal_file}")
    _logger.info(f"disabled_modules     : {disabled_modules}")
    _logger.info(f"conversion           : {conversion}")
    _logger.info(f"mask                 : {mask}")
    _logger.info(f"double_pixels_action : {double_pixels_action}")
    _logger.info(f"geometry             : {geometry}")
    _logger.info(f"gap_pixels           : {gap_pixels}")
    _logger.info(f"compression          : {compression}")
    _logger.info(f"factor               : {factor}")
    _logger.info(f"downsample           : {downsample}")
    _logger.info(f"roi                  : {roi}")
    _logger.info(f"reduce pulseids      : {len(selected_pulse_ids)>0} {len(selected_pulse_ids)}")
    _logger.info(f"save ppicker events  : {save_ppicker_events_only}")

    if remove_raw_files:
        _logger.info(f"removing raw and temporary files {files_to_remove}")
        for file_remove in files_to_remove:
            os.remove(file_remove)



