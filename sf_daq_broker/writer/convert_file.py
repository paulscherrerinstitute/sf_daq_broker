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
    downsample       = detector_params.get("downsample", None)
    remove_raw_files = detector_params.get("remove_raw_files", False)

    if downsample is not None:
        if isinstance(downsample, list):
            downsample = tuple(downsample)
        if not (isinstance(downsample, tuple) and len(downsample) == 2 and isinstance(downsample[0], int) and isinstance(downsample[1], int)):
            _logger.error(f'ignoring invalid "downsample" parameter (expected tuple of length two, got {downsample} instead)')
            downsample = None

    if conversion:
        double_pixels_action = detector_params.get("double_pixels_action", "mask")
        factor               = detector_params.get("factor", None)
        gap_pixels           = detector_params.get("gap_pixels", True)
        geometry             = detector_params.get("geometry", False)
        mask                 = detector_params.get("mask", True)
    else:
        double_pixels_action = "keep"
        factor               = None
        gap_pixels           = False
        geometry             = False
        mask                 = False

    roi = detector_params.get("roi", None)
    save_ppicker_events_only = detector_params.get("save_ppicker_events_only", False)
    selected_pulse_ids = data.get("selected_pulse_ids", [])

    n_selected_pulse_ids = len(selected_pulse_ids)

    files_to_remove = set()

    if conversion or disabled_modules or save_ppicker_events_only or selected_pulse_ids:
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
            if selected_pulse_ids:
                good_frames = []
                is_good_frames = juf["is_good_frame"]
                det_pulse_ids = juf["pulse_id"]
                for pulse_index in range(n_input_frames):
                    if is_good_frames[pulse_index] != 0 and det_pulse_ids[pulse_index][0] in selected_pulse_ids:
                        good_frames.append(pulse_index)
            else:
                good_frames = np.nonzero(juf["is_good_frame"])[0]


            if save_ppicker_events_only:
                good_frames_filtered = []
                daq_recs = juf["daq_rec"]
                for pulse_index in good_frames:
                    daq_rec = daq_recs[pulse_index][0]
#                    event_fel      = bool((daq_rec>>18) & 1)
                    event_ppicker  = bool((daq_rec>>19) & 1)
#                    if event_fel and event_ppicker:
                    if event_ppicker:
                        good_frames_filtered.append(pulse_index)

                if not np.array_equal(good_frames, good_frames_filtered):
                    excluded_indexes = set(good_frames) - set(good_frames_filtered)
                    excluded_indexes = list(excluded_indexes)
                    n_excluded_indexes = len(excluded_indexes)
                    good_frames = good_frames_filtered
                else:
                    n_excluded_indexes = "no"

                _logger.info(f"{n_excluded_indexes} frames were dropped due to filter on pulse picker event")


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
                    batch_size=35,
                )
            else:
                _logger.info("no output frames selected, thus no processed data file produced (raw data file will be kept)")
                remove_raw_files = False

    else:
        with h5py.File(file_in, "r") as juf:
            n_input_frames = len(juf[f"data/{detector_name}/data"])
            good_frames = np.nonzero(juf[f"data/{detector_name}/is_good_frame"])[0]
            n_output_frames = len(good_frames)


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
    _logger.info(f"reduce pulseids      : {n_selected_pulse_ids > 0} {n_selected_pulse_ids}")
    _logger.info(f"save ppicker events  : {save_ppicker_events_only}")

    if remove_raw_files:
        _logger.info(f"removing raw data files: {files_to_remove}")
        for file_remove in files_to_remove:
            os.remove(file_remove)



