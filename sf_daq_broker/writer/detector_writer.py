import logging
import os
from datetime import datetime
from time import time, sleep

import numpy as np
import h5py
import subprocess

from shutil import copyfile

try:
    import ujson as json
except:
    _logger.warning("There is no ujson in this environment. Performance will suffer.")
    import json

from sf_daq_broker import config, utils

from sf_daq_broker.writer.export_file import convert_file
from sf_daq_broker.detector.make_crystfel_list import make_crystfel_list

_logger = logging.getLogger("broker_writer")

PEDESTAL_SPECIFIC = { "JF02T09V02" : {"number_bad_modules" : 1},
                      "JF05T01V01" : {"number_bad_modules" : 1},
                      "JF06T08V02" : {"add_pixel_mask" : "/sf/alvra/config/jungfrau/pixel_mask/JF06T08V01/mask_2lines_module3.h5"},
                      "JF06T32V02" : {"number_bad_modules" : 1},
                      "JF07T32V01" : {"add_pixel_mask" : "/sf/bernina/config/jungfrau/pixel_mask/JF07T32V01/pixel_mask_13_full.h5"},
                      "JF10T01V01" : {"number_bad_modules" : 1},
                      "JF11T04V01" : {"number_bad_modules" : 2} }

# "JF03T01V02" : {"add_pixel_mask" : "/sf/bernina/config/jungfrau/pixel_mask/JF03T01V02/pixel_mask_half_chip.h5"},

def detector_retrieve(request, output_file_detector):

    detector = request["detector_name"]

    det_start_pulse_id = request["det_start_pulse_id"]
    det_stop_pulse_id  = request["det_stop_pulse_id"]
    rate_multiplicator = request["rate_multiplicator"]
    run_file_json      = request["run_file_json"]
    path_to_pgroup     = request["path_to_pgroup"]
    run_info_directory = request["run_info_directory"]

    detector_config_file = f'/gpfs/photonics/swissfel/buffer/config/{detector}.json'

    det_conversion  = request["detectors"][detector].get("adc_to_energy", False)
    det_compression = request["detectors"][detector].get("compression", False)
    det_number_disabled_modules = len(request["detectors"][detector].get("disabled_modules", []))

    det_save_ppicker_events_only = request["detectors"][detector].get("save_ppicker_events_only", False)

    det_number_selected_pulse_ids = len(request.get("selected_pulse_ids", []))

    convert_ju_file = False
    if det_conversion or det_compression or det_number_disabled_modules>0 or det_number_selected_pulse_ids>0 or det_save_ppicker_events_only:
        convert_ju_file = True

    raw_file_name = output_file_detector 
    if convert_ju_file:
        detector_filename = os.path.basename(raw_file_name)
        detector_dir = os.path.dirname(os.path.dirname(raw_file_name))
        raw_file_name = f'{detector_dir}/raw_data/{detector_filename}'
        raw_dir = os.path.dirname(raw_file_name)
        if not os.path.isdir(raw_dir):
            os.makedirs(raw_dir, exist_ok=True)

    number_modules = int(detector[5:7])
    retrieve_command_from_buffer = f'/home/dbe/bin/sf_writer {raw_file_name} /gpfs/photonics/swissfel/buffer/{detector} {number_modules} {det_start_pulse_id} {det_stop_pulse_id} {rate_multiplicator}'
    _logger.info("Starting detector retrieve from buffer %s " % retrieve_command_from_buffer)
    time_start = time()
    process=subprocess.run(retrieve_command_from_buffer.split(), capture_output=True)
    _logger.info(f"Retrieve Time : {time()-time_start}")
    _logger.info("Finished retrieve from the buffer")

    if "directory_name" in request and request["directory_name"] == "JF_pedestals":
        # sleep, to make sure h5 file is readable (strange but got problem rarely trying to read it)
        sleep(60)

        time_start = time()
        if detector in PEDESTAL_SPECIFIC:
            create_pedestal_file(filename=raw_file_name, directory=os.path.dirname(raw_file_name), **PEDESTAL_SPECIFIC[detector])
        else:
            create_pedestal_file(filename=raw_file_name, directory=os.path.dirname(raw_file_name))
        _logger.info(f"Pedestal Time : {time()-time_start}")
        request_time = request["request_time"]
        detector_config_file = f'/gpfs/photonics/swissfel/buffer/config/{detector}.json'
        res_file_name = raw_file_name[:-3]+".res.h5"
        copy_pedestal_file(request_time, res_file_name, detector, detector_config_file)
        copy_calibration_files(res_file_name, detector_config_file)

    if convert_ju_file:
        output_dir = os.path.dirname(output_file_detector)
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        _logger.info(f'Will do file conversion {raw_file_name} {output_file_detector} {run_file_json} {detector_config_file}')
        time_start = time()
        try:
            convert_file(raw_file_name, output_file_detector, run_file_json, detector_config_file)
        except Exception as e:
            _logger.error("Conversion failed")
            _logger.error(f"Error message : {e}")
        _logger.info(f"Conversion Time : {time()-time_start}")

        crystfel_lists = request["detectors"][detector].get("crystfel_lists_laser", False)
        if crystfel_lists:
           make_crystfel_list(output_file_detector, run_file_json, detector) 


def create_pedestal_file(filename="pedestal.h5", X_test_pixel=0, Y_test_pixel=0, nFramesPede=1000, 
                         number_frames=10000, frames_average=1000, 
                         directory="./", gain_check=1, add_pixel_mask=None, number_bad_modules=0):

    if not (os.path.isfile(filename) and os.access(filename, os.R_OK)):
        _logger.info("Pedestal file {} not found, exit".format(filename))
        return

    with h5py.File(filename, "r") as f:

        detector_name = (f.get("general/detector_name")[()]).decode('UTF-8')
        n_bad_modules = number_bad_modules

        data_location = "data/" + detector_name + "/data"
        daq_recs_location = "data/" + detector_name + "/daq_rec"
        is_good_frame_location = "data/" + detector_name + "/is_good_frame"


        numberOfFrames = len(f[data_location])
        (sh_y, sh_x) = f[data_location][0].shape
        nModules = (sh_x * sh_y) // (1024 * 512)
        if (nModules * 1024 * 512) != (sh_x * sh_y):
            _logger.error(" {} : Something very strange in the data, Jungfrau consists of (1024x512) modules, while data has {}x{}".format(detector_name, sh_x, sh_y))
            return

        (tX, tY) = (X_test_pixel, Y_test_pixel)
        if tX < 0 or tX > (sh_x - 1):
            tX = 0
        if tY < 0 or tY > (sh_y - 1):
            tY = 0

        _logger.debug(" {} : test pixel is ( x y ): {}x{}".format(detector_name, tX, tY))
        _logger.info(" {} : In pedestal file {} there are {} frames".format(detector_name, filename, numberOfFrames + 1))
        _logger.debug(" {} :   data has the following shape: {}, type: {}, {} modules ({} bad modules)".format(detector_name, f[data_location][0].shape, f[data_location][0].dtype, nModules, n_bad_modules))

        pixelMask = np.zeros((sh_y, sh_x), dtype=int)

        adcValuesN = np.zeros((4, sh_y, sh_x))
        adcValuesNN = np.zeros((4, sh_y, sh_x))


        averagePedestalFrames = frames_average

        nMgain = [0] * 4

        gainCheck = -1
        highG0Check = 0
        printFalseGain = False
        nGoodFrames = 0
        nGoodFramesGain = 0

        analyzeFrames = min(numberOfFrames, number_frames)

        for n in range(analyzeFrames):

            if not f[is_good_frame_location][n]:
                continue

            nGoodFrames += 1

            daq_rec = (f[daq_recs_location][n])[0]

            image = f[data_location][n][:]
            frameData = (np.bitwise_and(image, 0b0011111111111111))
            gainData = np.bitwise_and(image, 0b1100000000000000) >> 14

            trueGain = ( (daq_rec & 0b11000000000000) >> 12 )
            highG0 = (daq_rec & 0b1)

            gainGoodAllModules = True
            if gain_check > 0:
                daq_recs = f[daq_recs_location][n]
                for i in range(len(daq_recs)):
                    if trueGain != ((daq_recs[i] & 0b11000000000000) >> 12) or highG0 != (daq_recs[i] & 0b1):
                        gainGoodAllModules = False

#            if highG0 == 1 and trueGain != 0:
#                gainGoodAllModules = False
#                _logger.info(" {} : Jungfrau is in the high G0 mode ({}), but gain settings is strange: {}".format( detector_name, highG0, trueGain))

            nFramesGain = np.sum(gainData==(trueGain))
            if nFramesGain < (nModules - 0.5 - n_bad_modules) * (1024 * 512):  # make sure that most are the modules are in correct gain 
                gainGoodAllModules = False
                _logger.debug(" {} : Too many bad pixels, skip the frame {}, true gain: {}(highG0: {}) ({});  gain0 : {}; gain1 : {}; gain2 : {}; undefined gain : {}".format( detector_name, n, trueGain, highG0, nFramesGain, np.sum(gainData==0), np.sum(gainData==1), np.sum(gainData==3), np.sum(gainData==2)))

            if not gainGoodAllModules:
                _logger.debug(" {} : In Frame Number {} : mismatch in modules and general settings, Gain: {} vs {}; HighG0: {} vs {} (or too many bad pixels)".format( detector_name, n, trueGain, ((daq_recs & 0b11000000000000) >> 12), highG0, (daq_recs & 0b1)))
                continue
            nGoodFramesGain += 1

            if gainData[tY][tX] != trueGain:
                if not printFalseGain:
                    _logger.info(" {} : Gain wrong for channel ({}x{}) should be {}, but {}. Frame {}. {} {}".format( detector_name, tX, tY, trueGain, gainData[tY][tX], n, trueGain, daq_rec))
                    printFalseGain = True
            else:
                if gainCheck != -1 and printFalseGain:
                    _logger.info(" {} : Gain was wrong for channel ({}x{}) in previous frames, but now correct : {}. Frame {}.".format( detector_name, tX, tY, gainData[tY, tX], n))
                printFalseGain = False

            if gainData[tY][tX] != gainCheck or highG0Check != highG0:
                _logger.info(" {} : Gain changed for ({}x{}) channel {} -> {} (highG0 setting: {} -> {}), frame number {}, match: {}".format( detector_name, tX, tY, gainCheck, gainData[tY][tX], highG0Check, highG0, n, gainData[tY][tX] == trueGain))
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


    _logger.info(" {} : {} frames analyzed, {} good frames, {} frames without settings mismatch. Gain frames distribution (0,1,2,3,HG0) : ({})".format( detector_name, analyzeFrames, nGoodFrames, nGoodFramesGain, nMgain))

    if add_pixel_mask != None:
       if (os.path.isfile(add_pixel_mask) and os.access(add_pixel_mask, os.R_OK)):
           additional_pixel_mask = np.zeros((2,2))
           with h5py.File(add_pixel_mask, "r") as additional_pixel_mask_file:
               additional_pixel_mask = np.array(additional_pixel_mask_file["pixel_mask"])
           _logger.info("Will add additional masked pixels from file %s , number %d " % (add_pixel_mask, np.sum(additional_pixel_mask == 1)))
           if additional_pixel_mask.shape == pixelMask.shape:
               pixelMask[additional_pixel_mask == 1] |= (1 << 5)
           else:
               _logger.error(" shape of additional pixel mask ({}) doesn't match current ({})".format( additional_pixel_mask.shape, pixelMask.shape))
       else:
           _logger.error(" Specified addition file with pixel mask not found or not reachable {}".format( add_pixel_mask))

    fileNameIn = os.path.splitext(os.path.basename(filename))[0]
    full_fileNameOut = directory + "/" + fileNameIn + ".res.h5"
    _logger.info(" {} : Output file with pedestal corrections in: {}".format( detector_name, full_fileNameOut))

    with h5py.File(full_fileNameOut, "w") as outFile:

        gains = [None] * 3
        gainsRMS = [None] * 3

        for gain in range(4):
            if gain == 2:
                continue
            g = gain if gain < 3 else (gain-1)
            numberFramesAverage = max(1, min(averagePedestalFrames, nMgain[gain]))
            mean = adcValuesN[gain] / float(numberFramesAverage)
            mean2 = adcValuesNN[gain] / float(numberFramesAverage)
            variance = mean2 - np.float_power(mean, 2)
            stdDeviation = np.sqrt(variance)
            _logger.debug(" {} : gain {} values results (pixel ({},{}) : {} {}".format( detector_name, gain, tY, tX, mean[tY][tX], stdDeviation[tY][tX]))
            gains[g] = mean
            gainsRMS[g] = stdDeviation

            pixelMask[np.isclose(stdDeviation,0)] |= (1 << (6 + g))

        dset = outFile.create_dataset('pixel_mask', data=pixelMask)
        dset = outFile.create_dataset('gains', data=gains)
        dset = outFile.create_dataset('gainsRMS', data=gainsRMS)

    _logger.info(" {} : Number of good pixels: {} from {} in total ({} bad pixels)".format( detector_name, np.sum(pixelMask == 0), sh_x * sh_y, (sh_x * sh_y - np.sum(pixelMask == 0))))


def copy_pedestal_file(request_time, file_pedestal, detector, detector_config_file):

    PEDESTAL_DIRECTORY="/sf/jungfrau/data/pedestal"

    request_time=datetime.strptime(request_time, '%Y-%m-%d %H:%M:%S.%f')

    if not os.path.isdir(f'{PEDESTAL_DIRECTORY}/{detector}'):
        os.mkdir(f'{PEDESTAL_DIRECTORY}/{detector}')

    out_name = f'{PEDESTAL_DIRECTORY}/{detector}/{request_time.strftime("%Y%m%d_%H%M%S")}.h5'
    copyfile(file_pedestal, out_name)

    _logger.info(f'Copied resulting pedestal file {file_pedestal} to {out_name}')

    if not os.path.exists(detector_config_file):
        _logger.error(f'stream file {detector_config_file} does not exists, exiting')
        return

    with open(detector_config_file, "r") as stream_file:
        det = json.load(stream_file)

    print(f'Changing in stream file {detector_config_file} pedestal from {det["pedestal_file"]} to {out_name}')

    det["pedestal_file"] = out_name

    with open(detector_config_file, "w") as write_file:
        json.dump(det, write_file, indent=4)


def copy_calibration_files(pedestal_file, detector_config_file):

    with open(detector_config_file, "r") as stream_file:
        det_config = json.load(stream_file)

    detector = det_config["detector_name"]

    pedestal_directory = os.path.dirname(pedestal_file)
    gain_directory = f'{pedestal_directory}/gainMaps'
    pixel_mask_directory = f'{pedestal_directory}/pixel_mask'

    gain_file = det_config.get("gain_file", None)
 
    if gain_file is not None:
        if not os.path.isdir(gain_directory):
            os.makedirs(gain_directory)
        gain_file_copy = f'{gain_directory}/{detector}.h5'
        if not os.path.exists(gain_file_copy):
            copyfile(gain_file, gain_file_copy)    

    pixel_mask_file = None
    if detector in PEDESTAL_SPECIFIC:
        pixel_mask_file = PEDESTAL_SPECIFIC[detector].get("add_pixel_mask", None)

    if pixel_mask_file is not None:
        if not os.path.isdir(pixel_mask_directory):
            os.makedirs(pixel_mask_directory)
        pixel_mask_file_copy = f'{pixel_mask_directory}/{detector}.h5'
        if not os.path.exists(pixel_mask_file_copy):
            copyfile(pixel_mask_file, pixel_mask_file_copy)

        

