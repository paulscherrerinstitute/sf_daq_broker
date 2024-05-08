import logging
import os
import shutil
import subprocess
from datetime import datetime
from shutil import copyfile
from time import sleep, time

import h5py
import numpy as np

from sf_daq_broker.detector.make_crystfel_list import make_crystfel_list
from sf_daq_broker.detector.store_dap_info import store_dap_info
from sf_daq_broker.writer.convert_file import convert_file
from sf_daq_broker.utils import json_save, json_load


_logger = logging.getLogger("broker_writer")


PEDESTAL_SPECIFIC = {
    "JF02T09V02" : {"number_bad_modules" : 1},
#    "JF03T01V02" : {"add_pixel_mask" : "/sf/bernina/config/jungfrau/pixel_mask/JF03T01V02/pixel_mask_half_chip.h5"},
    "JF05T01V01" : {"number_bad_modules" : 1},
    "JF06T08V02" : {"add_pixel_mask" : "/sf/alvra/config/jungfrau/pixel_mask/JF06T08V01/mask_2lines_module3.h5"},
    "JF06T32V02" : {"number_bad_modules" : 1},
    "JF07T32V01" : {"add_pixel_mask" : "/sf/bernina/config/jungfrau/pixel_mask/JF07T32V01/pixel_mask_13_full.h5"},
    "JF10T01V01" : {"number_bad_modules" : 1},
    "JF11T04V01" : {"number_bad_modules" : 2},
    "JF18T01V01" : {"number_bad_modules" : 1}
}

TMPDIR = "/gpfs/photonics/swissfel/daqtmp"
TMP_SPACE_THRESH = 1e12 # 1TB



def detector_retrieve(request, output_file_detector):
    detector_name      = request["detector_name"]
    det_start_pulse_id = request["det_start_pulse_id"]
    det_stop_pulse_id  = request["det_stop_pulse_id"]
    rate_multiplicator = request["rate_multiplicator"]
    run_file_json      = request["run_file_json"]
#    path_to_pgroup     = request["path_to_pgroup"]
#    run_info_directory = request["run_info_directory"]

    beamline           = request.get("beamline", None)
    pgroup             = request.get("pgroup", None)
    directory_name     = request.get("directory_name", None)
    selected_pulse_ids = request.get("selected_pulse_ids", [])

    detector_params = request["detectors"][detector_name]

    adc_to_energy            = detector_params.get("adc_to_energy", False)
    compression              = detector_params.get("compression", False)
    disabled_modules         = detector_params.get("disabled_modules", [])
    roi                      = detector_params.get("roi", {})
    save_dap_results         = detector_params.get("save_dap_results", False)
    save_ppicker_events_only = detector_params.get("save_ppicker_events_only", False)

    # use SSD tmp storage only if raw files are removed
    use_tmp = detector_params.get("remove_raw_files", False)

    # get free space in SSD tmp storage, if smaller than threshold do not use it
    _tmp_space_total, _tmp_space_used, tmp_space_free = shutil.disk_usage(TMPDIR)
    if tmp_space_free < TMP_SPACE_THRESH:
        use_tmp = False

    pedestal_run = (directory_name == "JF_pedestals")

    if save_dap_results and not pedestal_run:
        file_name_out = output_file_detector[:-3] + ".dap"
        store_dap_info(beamline, pgroup, detector_name, det_start_pulse_id, det_stop_pulse_id, file_name_out)

    convert_ju_file = any((
        adc_to_energy,
        compression,
        disabled_modules,
        roi,
        save_ppicker_events_only,
        selected_pulse_ids
    ))

    if convert_ju_file:
        detector_filename = os.path.basename(output_file_detector)
        detector_dir = os.path.dirname(os.path.dirname(output_file_detector))
        raw_file_name = f"{detector_dir}/raw_data/{detector_filename}"
        if use_tmp:
            # flatten folder structure so that there are no empty folders after removal
            flat_raw_file_name = raw_file_name.replace("/", "_")
            raw_file_name = f"{TMPDIR}/{flat_raw_file_name}"
        raw_dir = os.path.dirname(raw_file_name)
        os.makedirs(raw_dir, exist_ok=True)
    else:
        raw_file_name = output_file_detector

    number_modules = int(detector_name[5:7])

    command_retrieve_from_buffer = (
        "/home/dbe/bin/sf_writer",
        raw_file_name,
        f"/gpfs/photonics/swissfel/buffer/{detector_name}",
        number_modules,
        det_start_pulse_id,
        det_stop_pulse_id,
        rate_multiplicator
    )

    command_retrieve_from_buffer = tuple(str(i) for i in command_retrieve_from_buffer)

    printable_command_retrieve_from_buffer = " ".join(command_retrieve_from_buffer)
    _logger.info(f"executing detector retrieval from buffer: {printable_command_retrieve_from_buffer}")

    time_start = time()
    _process = subprocess.run(command_retrieve_from_buffer, capture_output=True)
    delta_time = time() - time_start

    _logger.info(f"detector retrieval from buffer took {delta_time} seconds")

    detector_config_file = f"/gpfs/photonics/swissfel/buffer/config/{detector_name}.json"


    if pedestal_run:
        sleep(5)

        specific_kwargs = PEDESTAL_SPECIFIC.get(detector_name, {})
        time_start = time()
        create_pedestal_file(filename=raw_file_name, directory=os.path.dirname(raw_file_name), **specific_kwargs)
        delta_time = time() - time_start
        _logger.info(f"pedestal creation took {delta_time} seconds")

        request_time = request["request_time"]
        res_file_name = raw_file_name[:-3] + ".res.h5"
        copy_pedestal_file(request_time, res_file_name, detector_name, detector_config_file)
        copy_calibration_files(res_file_name, detector_config_file)


    if convert_ju_file:
        output_dir = os.path.dirname(output_file_detector)
        os.makedirs(output_dir, exist_ok=True)

        _logger.info(f"performing file conversion: {raw_file_name}, {output_file_detector}, {run_file_json}, {detector_config_file}")

        time_start = time()

        try:
            convert_file(raw_file_name, output_file_detector, run_file_json, detector_config_file)
        except Exception:
            _logger.exception("file conversion failed")

        delta_time = time() - time_start
        _logger.info(f"file conversion took {delta_time} seconds")


        crystfel_lists_laser = detector_params.get("crystfel_lists_laser", False)
        if crystfel_lists_laser:
            make_crystfel_list(output_file_detector, run_file_json, detector_name)


    if not pedestal_run and save_dap_results:
        file_name_out = output_file_detector[:-3] + ".dap"
        store_dap_info(beamline, pgroup, detector_name, det_start_pulse_id, det_stop_pulse_id, file_name_out)



def create_pedestal_file(
    filename="pedestal.h5",
    X_test_pixel=0,
    Y_test_pixel=0,
    frames_average=1000,
    directory="./",
    gain_check=True,
    add_pixel_mask=None,
    number_bad_modules=0
):
    if not os.path.isfile(filename) or not os.access(filename, os.R_OK):
        _logger.info(f"cannot create pedestal file: input file {filename} not found")
        return

    with h5py.File(filename, "r") as h5f:
        detector_name = h5f["general/detector_name"][()]
        detector_name = detector_name.decode("UTF-8")

        data_location          = f"data/{detector_name}/data"
        daq_recs_location      = f"data/{detector_name}/daq_rec"
        is_good_frame_location = f"data/{detector_name}/is_good_frame"

        # for larger detectors and pedestalmode=True, data may be too large to be loaded at once
        #TODO: check memory usage and only if possible load at once for better performance
        f_data          = h5f[data_location]
        f_is_good_frame = h5f[is_good_frame_location][:]
        f_daq_recs      = h5f[daq_recs_location][:]

        f_data0 = f_data[0]

        sh_y, sh_x = f_data0.shape
        nModules = (sh_x * sh_y) // (1024 * 512)
        if (nModules * 1024 * 512) != (sh_x * sh_y):
            _logger.error(f"{detector_name}: shape mismatch: Jungfrau modules have shape 1024x512, while data has shape {sh_x}x{sh_y}")
            return

        tX = X_test_pixel
        tY = Y_test_pixel
        if tX < 0 or tX > (sh_x - 1):
            tX = 0
        if tY < 0 or tY > (sh_y - 1):
            tY = 0

        _logger.debug(f"{detector_name}: test pixel is at (x, y): ({tX}, {tY})")

        numberOfFrames = len(f_data)
        _logger.info(f"{detector_name}: pedestal file {filename} contains {numberOfFrames + 1} frames")

        data_shape = f_data0.shape
        data_dtype = f_data0.dtype
        _logger.debug(f"{detector_name}: data has shape: {data_shape}, type: {data_dtype}, {nModules} modules ({number_bad_modules} bad modules)")

        pixelMask = np.zeros((sh_y, sh_x), dtype=int)

        adcValuesN  = np.zeros((4, sh_y, sh_x))
        adcValuesNN = np.zeros((4, sh_y, sh_x))

        nMgain = [0] * 4

        gainCheck = -1
        highG0Check = 0
        printFalseGain = False
        nGoodFrames = 0
        nGoodFramesGain = 0

        for n in range(numberOfFrames):

            if not f_is_good_frame[n]:
                continue

            nGoodFrames += 1

            image = f_data[n]
            frameData = np.bitwise_and(image, 0b0011111111111111)
            gainData  = np.bitwise_and(image, 0b1100000000000000) >> 14

            daq_rec = f_daq_recs[n][0]
            trueGain = (daq_rec & 0b11000000000000) >> 12
            highG0 = daq_rec & 0b1

            gainGoodAllModules = True
            if gain_check:
                daq_recs = f_daq_recs[n]
                for dr in daq_recs:
                    trueGain_found = (dr & 0b11000000000000) >> 12
                    highG0_found = dr & 0b1
                    if trueGain != trueGain_found or highG0 != highG0_found:
                        gainGoodAllModules = False

            if not gainGoodAllModules:
                trueGain_found = (daq_recs & 0b11000000000000) >> 12
                highG0_found = daq_recs & 0b1
                _logger.debug(f"{detector_name}: skipping frame {n}: mismatch between modules and general settings: gain: {trueGain} vs {trueGain_found}, highG0: {highG0} vs {highG0_found}")
                continue

#            if highG0 == 1 and trueGain != 0:
#                gainGoodAllModules = False
#                _logger.info(f"{detector_name}: skipping frame {n}: Jungfrau is in high G0 mode ({highG0}), but gain settings is: {trueGain}")
#                continue

            nFramesGain = np.sum(gainData == trueGain)
            # make sure that most are the modules are in correct gain
            if nFramesGain < (nModules - 0.5 - number_bad_modules) * (1024 * 512):
                gainGoodAllModules = False
                gain0 = np.sum(gainData == 0)
                gain1 = np.sum(gainData == 1)
                gain2 = np.sum(gainData == 3)
                gain_undefined = np.sum(gainData == 2)
                _logger.debug(f"{detector_name}: skipping frame {n}: too many bad pixels (true gain: {trueGain} ({nFramesGain}), highG0: {highG0}, gain0: {gain0}, gain1: {gain1}, gain2: {gain2}, undefined gain: {gain_undefined})")
                continue

            nGoodFramesGain += 1

            gainData_tXtY = gainData[tY][tX]

            if gainData_tXtY != trueGain:
                if not printFalseGain:
                    _logger.info(f"{detector_name}: frame {n}: wrong gain for test pixel ({tX}, {tY}): expected {trueGain} but found {gainData_tXtY}")
                    printFalseGain = True
            else:
                if gainCheck != -1 and printFalseGain:
                    _logger.info(f"{detector_name}: frame {n}: wrong gain for test pixel ({tX}, {tY}) in previous frame, but correct in this frame {gainData[tY, tX]}")
                printFalseGain = False

            if gainCheck != gainData_tXtY or highG0Check != highG0:
                _logger.info(f"{detector_name}: frame {n}: gain changed for test pixel ({tX}, {tY}): {gainCheck} -> {gainData_tXtY} (highG0: {highG0Check} -> {highG0}), match: {gainData_tXtY == trueGain}")
                gainCheck = gainData_tXtY
                highG0Check = highG0

            if gainGoodAllModules:
                pixelMask[gainData != trueGain] |= (1 << (trueGain + 4 * highG0))
                #trueGain += 4 * highG0
                nMgain[trueGain] += 1

                if nMgain[trueGain] > frames_average:
                    adcValuesN[trueGain]  -= adcValuesN[trueGain]  / frames_average
                    adcValuesNN[trueGain] -= adcValuesNN[trueGain] / frames_average

                adcValuesN[trueGain]  += frameData
                adcValuesNN[trueGain] += np.float_power(frameData, 2)


        _logger.info(f"{detector_name}: {numberOfFrames} frames analyzed, {nGoodFrames} good frames, {nGoodFramesGain} frames without settings mismatch; gain frames distribution (0, 1, 2, 3, HG0): ({nMgain})")

        if add_pixel_mask is not None:
            if os.path.isfile(add_pixel_mask) and os.access(add_pixel_mask, os.R_OK):
                additional_pixel_mask = np.zeros((2, 2))
                with h5py.File(add_pixel_mask, "r") as additional_pixel_mask_file:
                    additional_pixel_mask = additional_pixel_mask_file["pixel_mask"]
                    additional_pixel_mask = np.array(additional_pixel_mask)
                number = np.sum(additional_pixel_mask == 1)
                _logger.info(f"{detector_name}: adding additional pixel mask from file {add_pixel_mask}, number {number}")
                if additional_pixel_mask.shape == pixelMask.shape:
                    pixelMask[additional_pixel_mask == 1] |= (1 << 5)
                else:
                    _logger.error(f"{detector_name}: shape of additional pixel mask ({additional_pixel_mask.shape}) does not match current pixel mask ({pixelMask.shape})")
            else:
                _logger.error(f"{detector_name}: specified file with additional pixel mask {add_pixel_mask} not found or not readable")

        fileNameIn = os.path.splitext(os.path.basename(filename))[0]
        full_fileNameOut = directory + "/" + fileNameIn + ".res.h5"
        _logger.info(f"{detector_name}: output file with pedestal corrections: {full_fileNameOut}")

        gains    = [None] * 3
        gainsRMS = [None] * 3

        for gain in (0, 1, 3):
            gv = 2 if gain == 3 else gain
            numberFramesAverage = max(1, min(frames_average, nMgain[gain]))
            mean  = adcValuesN[gain]  / float(numberFramesAverage)
            mean2 = adcValuesNN[gain] / float(numberFramesAverage)
            variance = mean2 - np.float_power(mean, 2)
            stdDeviation = np.sqrt(variance)
            _logger.debug(f"{detector_name}: results for gain {gain}: test pixel ({tY}, {tX}), mean: {mean[tY][tX]}, stddev: {stdDeviation[tY][tX]}")
            gains[gv] = mean
            gainsRMS[gv] = stdDeviation

            pixelMask[np.isclose(stdDeviation, 0)] |= (1 << (6 + gv))

        with h5py.File(full_fileNameOut, "w") as outFile:
            outFile.create_dataset("pixel_mask", data=pixelMask)
            outFile.create_dataset("gains",      data=gains)
            outFile.create_dataset("gainsRMS",   data=gainsRMS)

        ngood = np.sum(pixelMask == 0)
        ntotal = sh_x * sh_y
        nbad = ntotal - ngood
        _logger.info(f"{detector_name}: number of good pixels: {ngood} from {ntotal} in total ({nbad} bad pixels)")



def copy_pedestal_file(request_time, file_pedestal, detector, detector_config_file):
    PEDESTAL_DIRECTORY="/sf/jungfrau/data/pedestal"

    os.makedirs(f"{PEDESTAL_DIRECTORY}/{detector}", exist_ok=True)

    request_time = datetime.strptime(request_time, "%Y-%m-%d %H:%M:%S.%f")
    request_time_formatted = request_time.strftime("%Y%m%d_%H%M%S")

    out_name = f"{PEDESTAL_DIRECTORY}/{detector}/{request_time_formatted}.h5"

    _logger.info(f"copying pedestal file {file_pedestal} to {out_name}")
    copyfile(file_pedestal, out_name)

    if not os.path.exists(detector_config_file):
        _logger.error(f"cannot update currently used pedestal: stream config file {detector_config_file} does not exists")
        return

    det = json_load(detector_config_file)
    old_pedestal_file = det["pedestal_file"]
    det["pedestal_file"] = out_name

    _logger.info(f"updating stream config file {detector_config_file}: change pedestal from {old_pedestal_file} to {out_name}")
    json_save(det, detector_config_file)


def copy_calibration_files(pedestal_file, detector_config_file):
    pedestal_directory = os.path.dirname(pedestal_file)
    gain_directory = f"{pedestal_directory}/gainMaps"
    pixel_mask_directory = f"{pedestal_directory}/pixel_mask"

    det_config = json_load(detector_config_file)
    detector_name = det_config["detector_name"]

    gain_file = det_config.get("gain_file", None)

    if gain_file:
        os.makedirs(gain_directory, exist_ok=True)
        gain_file_copy = f"{gain_directory}/{detector_name}.h5"
        if not os.path.exists(gain_file_copy):
            copyfile(gain_file, gain_file_copy)

    specific = PEDESTAL_SPECIFIC.get(detector_name, {})
    pixel_mask_file = specific.get("add_pixel_mask", None)

    if pixel_mask_file:
        os.makedirs(pixel_mask_directory, exist_ok=True)
        pixel_mask_file_copy = f"{pixel_mask_directory}/{detector_name}.h5"
        if not os.path.exists(pixel_mask_file_copy):
            copyfile(pixel_mask_file, pixel_mask_file_copy)



