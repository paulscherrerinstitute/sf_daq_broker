import logging
import os
import subprocess
from datetime import datetime
from shutil import copyfile
from time import sleep, time

import h5py
import numpy as np

_logger = logging.getLogger("broker_writer")

try:
    import ujson
except ImportError:
    _logger.warning("There is no ujson in this environment. Performance will suffer.")
else:
    del ujson

from sf_daq_broker.detector.make_crystfel_list import make_crystfel_list, store_dap_info
from sf_daq_broker.writer.export_file import convert_file
from sf_daq_broker.utils import json_save, json_load


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



def detector_retrieve(request, output_file_detector):
    detector_name      = request["detector_name"]
    det_start_pulse_id = request["det_start_pulse_id"]
    det_stop_pulse_id  = request["det_stop_pulse_id"]
    rate_multiplicator = request["rate_multiplicator"]
    run_file_json      = request["run_file_json"]
#    path_to_pgroup     = request["path_to_pgroup"]
#    run_info_directory = request["run_info_directory"]

    detector_config_file = f"/gpfs/photonics/swissfel/buffer/config/{detector_name}.json"

    detector_params = request["detectors"][detector_name]

    det_conversion  = detector_params.get("adc_to_energy", False)
    det_compression = detector_params.get("compression", False)

    disabled_modules = detector_params.get("disabled_modules", [])
    det_number_disabled_modules = len(disabled_modules)

    roi = detector_params.get("roi", {})
    det_number_roi = len(roi)

    det_save_ppicker_events_only = detector_params.get("save_ppicker_events_only", False)

    selected_pulse_ids = request.get("selected_pulse_ids", [])
    det_number_selected_pulse_ids = len(selected_pulse_ids)

    beamline = request.get("beamline", None)
    pgroup   = request.get("pgroup", None)

    det_save_dap_results = detector_params.get("save_dap_results", False)

    pedestal_run = "directory_name" in request and request["directory_name"] == "JF_pedestals"

    if not pedestal_run and det_save_dap_results:
        file_name_out = output_file_detector[:-3] + ".dap"
        store_dap_info(beamline=beamline, pgroup=pgroup, detector=detector_name, start_pulse_id=det_start_pulse_id, stop_pulse_id=det_stop_pulse_id, file_name_out=file_name_out)


    convert_ju_file = det_conversion or det_compression or det_number_disabled_modules>0 or det_number_selected_pulse_ids>0 or det_save_ppicker_events_only or det_number_roi>0

    raw_file_name = output_file_detector
    if convert_ju_file:
        detector_filename = os.path.basename(raw_file_name)
        detector_dir = os.path.dirname(os.path.dirname(raw_file_name))
        raw_file_name = f"{detector_dir}/raw_data/{detector_filename}"
        raw_dir = os.path.dirname(raw_file_name)
        os.makedirs(raw_dir, exist_ok=True)

    number_modules = int(detector_name[5:7])

    retrieve_command_from_buffer = f"/home/dbe/bin/sf_writer {raw_file_name} /gpfs/photonics/swissfel/buffer/{detector_name} {number_modules} {det_start_pulse_id} {det_stop_pulse_id} {rate_multiplicator}"
    _logger.info(f"Starting detector retrieve from buffer {retrieve_command_from_buffer} ")
    retrieve_command_from_buffer = retrieve_command_from_buffer.split() #TODO: should probably use shlex.split
    time_start = time()
    _process = subprocess.run(retrieve_command_from_buffer, capture_output=True)
    _logger.info(f"Retrieve Time : {time()-time_start}")
    _logger.info("Finished retrieve from the buffer")


    if pedestal_run:
        sleep(5)

        specific_kwargs = PEDESTAL_SPECIFIC.get(detector_name, {})
        time_start = time()
        create_pedestal_file(filename=raw_file_name, directory=os.path.dirname(raw_file_name), **specific_kwargs)
        _logger.info(f"Pedestal Time : {time()-time_start}")

        request_time = request["request_time"]
        detector_config_file = f"/gpfs/photonics/swissfel/buffer/config/{detector_name}.json"
        res_file_name = raw_file_name[:-3] + ".res.h5"
        copy_pedestal_file(request_time, res_file_name, detector_name, detector_config_file)
        copy_calibration_files(res_file_name, detector_config_file)


    if convert_ju_file:
        output_dir = os.path.dirname(output_file_detector)
        os.makedirs(output_dir, exist_ok=True)
        _logger.info(f"Will do file conversion {raw_file_name} {output_file_detector} {run_file_json} {detector_config_file}")
        time_start = time()
        try:
            convert_file(raw_file_name, output_file_detector, run_file_json, detector_config_file)
        except Exception as e:
            _logger.error("Conversion failed")
            _logger.error(f"Error message : {e}")
        _logger.info(f"Conversion Time : {time()-time_start}")

        crystfel_lists = detector_params.get("crystfel_lists_laser", False)
        if crystfel_lists:
            make_crystfel_list(output_file_detector, run_file_json, detector_name)


    if not pedestal_run and det_save_dap_results:
        file_name_out = output_file_detector[:-3] + ".dap"
        store_dap_info(beamline=beamline, pgroup=pgroup, detector=detector_name, start_pulse_id=det_start_pulse_id, stop_pulse_id=det_stop_pulse_id, file_name_out=file_name_out)



def create_pedestal_file(
    filename="pedestal.h5",
    X_test_pixel=0,
    Y_test_pixel=0,
    _nFramesPede=1000, #TODO: what is nFramesPede for?
    number_frames=10000,
    frames_average=1000,
    directory="./",
    gain_check=1,
    add_pixel_mask=None,
    number_bad_modules=0
):

    if not os.path.isfile(filename) or not os.access(filename, os.R_OK):
        _logger.info(f"Pedestal file {filename} not found, exit")
        return

    with h5py.File(filename, "r") as f:
        detector_name = f.get("general/detector_name")[()]
        detector_name = detector_name.decode("UTF-8")
        n_bad_modules = number_bad_modules

        data_location          = "data/" + detector_name + "/data"
        daq_recs_location      = "data/" + detector_name + "/daq_rec"
        is_good_frame_location = "data/" + detector_name + "/is_good_frame"

        fdata = f[data_location]
        fdata0 = fdata[0]

        numberOfFrames = len(fdata)
        sh_y, sh_x = fdata0.shape
        nModules = (sh_x * sh_y) // (1024 * 512)
        if (nModules * 1024 * 512) != (sh_x * sh_y):
            _logger.error(f" {detector_name} : Something very strange in the data, Jungfrau consists of (1024x512) modules, while data has {sh_x}x{sh_y}")
            return

        tX = X_test_pixel
        tY = Y_test_pixel
        if tX < 0 or tX > (sh_x - 1):
            tX = 0
        if tY < 0 or tY > (sh_y - 1):
            tY = 0

        _logger.debug(f" {detector_name} : test pixel is ( x y ): {tX}x{tY}")
        _logger.info(f" {detector_name} : In pedestal file {filename} there are {numberOfFrames + 1} frames")

        data_shape = fdata0.shape
        data_dtype = fdata0.dtype
        _logger.debug(f" {detector_name} :   data has the following shape: {data_shape}, type: {data_dtype}, {nModules} modules ({n_bad_modules} bad modules)")

        pixelMask = np.zeros((sh_y, sh_x), dtype=int)

        adcValuesN  = np.zeros((4, sh_y, sh_x))
        adcValuesNN = np.zeros((4, sh_y, sh_x))

        averagePedestalFrames = frames_average

        nMgain = [0] * 4

        gainCheck = -1
        highG0Check = 0
        printFalseGain = False
        nGoodFrames = 0
        nGoodFramesGain = 0

        analyzeFrames = min(numberOfFrames, number_frames)

        f_is_good_frame = f[is_good_frame_location]
        f_daq_recs = f[daq_recs_location]

        for n in range(analyzeFrames):
            if not f_is_good_frame[n]:
                continue

            nGoodFrames += 1

            image = fdata[n][:]
            frameData = np.bitwise_and(image, 0b0011111111111111)
            gainData = np.bitwise_and(image, 0b1100000000000000) >> 14

            daq_rec = f_daq_recs[n][0]
            trueGain = (daq_rec & 0b11000000000000) >> 12
            highG0 = daq_rec & 0b1

            gainGoodAllModules = True
            if gain_check > 0:
                daq_recs = f_daq_recs[n]
                for dr in daq_recs:
                    if trueGain != ((dr & 0b11000000000000) >> 12) or highG0 != (dr & 0b1):
                        gainGoodAllModules = False

#            if highG0 == 1 and trueGain != 0:
#                gainGoodAllModules = False
#                _logger.info(" {} : Jungfrau is in the high G0 mode ({}), but gain settings is strange: {}".format( detector_name, highG0, trueGain))

            nFramesGain = np.sum(gainData==trueGain)
            if nFramesGain < (nModules - 0.5 - n_bad_modules) * (1024 * 512):  # make sure that most are the modules are in correct gain
                gainGoodAllModules = False
                gain0 = np.sum(gainData == 0)
                gain1 = np.sum(gainData == 1)
                gain2 = np.sum(gainData == 3)
                gain_undefined = np.sum(gainData == 2)
                _logger.debug(f" {detector_name} : Too many bad pixels, skip the frame {n}, true gain: {trueGain}(highG0: {highG0}) ({nFramesGain});  gain0 : {gain0}; gain1 : {gain1}; gain2 : {gain2}; undefined gain : {gain_undefined}")

            if not gainGoodAllModules:
                _logger.debug(f" {detector_name} : In Frame Number {n} : mismatch in modules and general settings, Gain: {trueGain} vs {(daq_recs & 0b11000000000000) >> 12}; HighG0: {highG0} vs {daq_recs & 0b1} (or too many bad pixels)")
                continue

            nGoodFramesGain += 1

            if gainData[tY][tX] != trueGain:
                if not printFalseGain:
                    _logger.info(f" {detector_name} : Gain wrong for channel ({tX}x{tY}) should be {trueGain}, but {gainData[tY][tX]}. Frame {n}. {trueGain} {daq_rec}")
                    printFalseGain = True
            else:
                if gainCheck != -1 and printFalseGain:
                    _logger.info(f" {detector_name} : Gain was wrong for channel ({tX}x{tY}) in previous frames, but now correct : {gainData[tY, tX]}. Frame {n}.")
                printFalseGain = False

            if gainData[tY][tX] != gainCheck or highG0Check != highG0:
                _logger.info(f" {detector_name} : Gain changed for ({tX}x{tY}) channel {gainCheck} -> {gainData[tY][tX]} (highG0 setting: {highG0Check} -> {highG0}), frame number {n}, match: {gainData[tY][tX] == trueGain}")
                gainCheck = gainData[tY][tX]
                highG0Check = highG0

            if gainGoodAllModules:
                pixelMask[gainData != trueGain] |= (1 << (trueGain+4*highG0))
                #trueGain += 4 * highG0
                nMgain[trueGain] += 1

                if nMgain[trueGain] > averagePedestalFrames:
                    adcValuesN[trueGain] -= adcValuesN[trueGain] / averagePedestalFrames
                    adcValuesNN[trueGain] -= adcValuesNN[trueGain] / averagePedestalFrames

                adcValuesN[trueGain] += frameData
                adcValuesNN[trueGain] += np.float_power(frameData, 2)


    _logger.info(f" {detector_name} : {analyzeFrames} frames analyzed, {nGoodFrames} good frames, {nGoodFramesGain} frames without settings mismatch. Gain frames distribution (0,1,2,3,HG0) : ({nMgain})")

    if add_pixel_mask is not None:
        if os.path.isfile(add_pixel_mask) and os.access(add_pixel_mask, os.R_OK):
            additional_pixel_mask = np.zeros((2, 2))
            with h5py.File(add_pixel_mask, "r") as additional_pixel_mask_file:
                additional_pixel_mask = additional_pixel_mask_file["pixel_mask"]
                additional_pixel_mask = np.array(additional_pixel_mask)
            number = np.sum(additional_pixel_mask == 1)
            _logger.info(f"Will add additional masked pixels from file {add_pixel_mask} , number {number} ")
            if additional_pixel_mask.shape == pixelMask.shape:
                pixelMask[additional_pixel_mask == 1] |= (1 << 5)
            else:
                _logger.error(f" shape of additional pixel mask ({additional_pixel_mask.shape}) does not match current ({pixelMask.shape})")
        else:
            _logger.error(f" Specified addition file with pixel mask not found or not reachable {add_pixel_mask}")

    fileNameIn = os.path.splitext(os.path.basename(filename))[0]
    full_fileNameOut = directory + "/" + fileNameIn + ".res.h5"
    _logger.info(f" {detector_name} : Output file with pedestal corrections in: {full_fileNameOut}")

    with h5py.File(full_fileNameOut, "w") as outFile:
        gains    = [None] * 3
        gainsRMS = [None] * 3

        for gain in range(4):
            if gain == 2:
                continue
            g = gain if gain < 3 else gain - 1
            numberFramesAverage = max(1, min(averagePedestalFrames, nMgain[gain]))
            mean = adcValuesN[gain] / float(numberFramesAverage)
            mean2 = adcValuesNN[gain] / float(numberFramesAverage)
            variance = mean2 - np.float_power(mean, 2)
            stdDeviation = np.sqrt(variance)
            _logger.debug(f" {detector_name} : gain {gain} values results (pixel ({tY},{tX}) : {mean[tY][tX]} {stdDeviation[tY][tX]}")
            gains[g] = mean
            gainsRMS[g] = stdDeviation

            pixelMask[np.isclose(stdDeviation,0)] |= (1 << (6 + g))

        outFile.create_dataset("pixel_mask", data=pixelMask)
        outFile.create_dataset("gains", data=gains)
        outFile.create_dataset("gainsRMS", data=gainsRMS)

    ngood = np.sum(pixelMask == 0)
    ntotal = sh_x * sh_y
    nbad = ntotal - ngood
    _logger.info(f" {detector_name} : Number of good pixels: {ngood} from {ntotal} in total ({nbad} bad pixels)")



def copy_pedestal_file(request_time, file_pedestal, detector, detector_config_file):
    PEDESTAL_DIRECTORY="/sf/jungfrau/data/pedestal"
    request_time=datetime.strptime(request_time, "%Y-%m-%d %H:%M:%S.%f")

    os.makedirs(f"{PEDESTAL_DIRECTORY}/{detector}", exist_ok=True)

    request_time_formatted = request_time.strftime("%Y%m%d_%H%M%S")
    out_name = f"{PEDESTAL_DIRECTORY}/{detector}/{request_time_formatted}.h5"
    copyfile(file_pedestal, out_name)

    _logger.info(f"Copied resulting pedestal file {file_pedestal} to {out_name}")

    if not os.path.exists(detector_config_file):
        _logger.error(f"stream file {detector_config_file} does not exists, exiting")
        return

    det = json_load(detector_config_file)

    old_pedestal_file = det["pedestal_file"]
    _logger.info(f"Changing in stream file {detector_config_file} pedestal from {old_pedestal_file} to {out_name}")

    det["pedestal_file"] = out_name

    json_save(det, detector_config_file)


def copy_calibration_files(pedestal_file, detector_config_file):
    det_config = json_load(detector_config_file)

    detector = det_config["detector_name"]

    pedestal_directory = os.path.dirname(pedestal_file)
    gain_directory = f"{pedestal_directory}/gainMaps"
    pixel_mask_directory = f"{pedestal_directory}/pixel_mask"

    gain_file = det_config.get("gain_file", None)

    if gain_file is not None:
        os.makedirs(gain_directory, exist_ok=True)
        gain_file_copy = f"{gain_directory}/{detector}.h5"
        if not os.path.exists(gain_file_copy):
            copyfile(gain_file, gain_file_copy)

    pixel_mask_file = None
    if detector in PEDESTAL_SPECIFIC:
        pixel_mask_file = PEDESTAL_SPECIFIC[detector].get("add_pixel_mask", None)

    if pixel_mask_file is not None:
        os.makedirs(pixel_mask_directory, exist_ok=True)
        pixel_mask_file_copy = f"{pixel_mask_directory}/{detector}.h5"
        if not os.path.exists(pixel_mask_file_copy):
            copyfile(pixel_mask_file, pixel_mask_file_copy)



