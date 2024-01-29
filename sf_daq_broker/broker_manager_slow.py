import logging
import os
import shutil
from datetime import datetime
from glob import glob
from time import sleep

import epics
from slsdet import Jungfrau, gainMode
from slsdet.enums import detectorSettings

from sf_daq_broker.detector.detector_config import configured_detectors_for_beamline
from sf_daq_broker.detector.power_on_detector import beamline_event_code
from sf_daq_broker.utils import ip_to_console, json_save, json_load
from .return_status import return_status


_logger = logging.getLogger(__name__)

conv_detector_settings = {
    detectorSettings.GAIN0: "normal",
    detectorSettings.HIGHGAIN0: "low_noise"
}

conv_detector_gain_settings = {
    gainMode.DYNAMIC: "dynamic",
    gainMode.FORCE_SWITCH_G1: "fixed_gain1",
    gainMode.FORCE_SWITCH_G2: "fixed_gain2"
}

conv_detector_settings_reverse = dict(zip(conv_detector_settings.values(), conv_detector_settings.keys()))
conv_detector_gain_settings_reverse = dict(zip(conv_detector_gain_settings.values(), conv_detector_gain_settings.keys()))



class DetectorManager:

    @return_status
    def get_detector_settings(self, request=None, remote_ip=None):
        if not request:
            raise RuntimeError("request parameters are empty")

        if not remote_ip:
            raise RuntimeError("can not identify from which machine request were made")

        beamline = ip_to_console(remote_ip)
        if not beamline:
            raise RuntimeError("can not determine from which console request came, rejected")

        allowed_detectors_beamline = configured_detectors_for_beamline(beamline)
        if not allowed_detectors_beamline:
            raise RuntimeError("request is made from beamline which doesnt have detectors")

        detector_name = request.get("detector_name", None)
        if not detector_name:
            raise RuntimeError("no detector name in the request")

        if detector_name not in allowed_detectors_beamline:
            raise RuntimeError(f"{detector_name} not belongs to the {beamline}")

        detector_number = int(detector_name[2:4])
        detector = Jungfrau(detector_number)

        exptime = detector.exptime
        detector_mode = conv_detector_settings.get(detector.settings, "unknown")
        delay = detector.delay
        gain_mode = conv_detector_gain_settings.get(detector.gainmode, "Error")

        res = {
            "status": "ok",
            "exptime": exptime,
            "detector_mode": detector_mode,
            "delay": delay,
            "gain_mode": gain_mode
        }
        return res


    @return_status
    def set_detector_settings(self, request=None, remote_ip=None):
        if not request:
            raise RuntimeError("request parameters are empty")

        if not remote_ip:
            raise RuntimeError("can not identify from which machine request were made")

        beamline = ip_to_console(remote_ip)
        if not beamline:
            raise RuntimeError("can not determine from which console request came, rejected")

        allowed_detectors_beamline = configured_detectors_for_beamline(beamline)
        if not allowed_detectors_beamline:
            raise RuntimeError("request is made from beamline which doesnt have detectors")

        detector_name = request.get("detector_name", None)
        if not detector_name:
            raise RuntimeError("no detector name in the request")

        if detector_name not in allowed_detectors_beamline:
            raise RuntimeError(f"{detector_name} not belongs to the {beamline}")

        detector_number = int(detector_name[2:4])
        detector = Jungfrau(detector_number)

        exptime       = request.get("exptime", None)
        detector_mode = request.get("detector_mode", None)
        delay         = request.get("delay", None)
        gain_mode     = request.get("gain_mode", None)

        event_code_pv_name = beamline_event_code[beamline]
        event_code_pv = epics.PV(event_code_pv_name)

        # stop triggering of the beamline detectors
        try:
            event_code_pv.put(255)
        except Exception as e:
            raise RuntimeError(f"can not stop detector trigger (due to: {e})") from e

        #sleep few second to give epics a chance to switch code
        sleep(4)

        try:
            event_code = int(event_code_pv.get())
        except Exception as e:
            raise RuntimeError(f"getting strange return from timing system {event_code_pv.get()} {event_code_pv_name} {beamline} (due to: {e})") from e

        if event_code != 255:
            raise RuntimeError("tried to stop detector trigger but failed")

        if exptime:
            detector.exptime = exptime
            _logger.info(f"setting exptime to {exptime}")

        if detector_mode:
            if detector_mode in conv_detector_settings_reverse:
                detector.settings = conv_detector_settings_reverse[detector_mode]
                _logger.info(f"settings detector settings to {conv_detector_settings_reverse[detector_mode]} ({detector_mode})")

        if delay:
            detector.delay = delay
            _logger.info(f"setting delay to {delay}")

        if gain_mode:
            if gain_mode in conv_detector_gain_settings_reverse:
                detector.gainmode = conv_detector_gain_settings_reverse[gain_mode]
                _logger.info(f"settings detector settings to {conv_detector_gain_settings_reverse[gain_mode]} ({gain_mode})")

        # start triggering
        event_code_pv.put(254)
        event_code_pv.disconnect()

        return "detector settings changed successfully"


    @return_status
    def copy_user_files(self, request=None, remote_ip=None):
        if not request:
            raise RuntimeError("request parameters are empty")

        if not remote_ip:
            raise RuntimeError("can not identify from which machine request were made")

        beamline = ip_to_console(remote_ip)
        if not beamline:
            raise RuntimeError("can not determine from which console request came, rejected")

        allowed_detectors_beamline = configured_detectors_for_beamline(beamline)
        if len(allowed_detectors_beamline) == 0:
            raise RuntimeError("request is made from beamline which doesnt have detectors")

        if "pgroup" not in request:
            raise RuntimeError("no pgroup in request parameters")

        pgroup = request["pgroup"]
        path_to_pgroup = f"/sf/{beamline}/data/{pgroup}/raw/"
        if os.path.exists(f"{path_to_pgroup}/run_info/CLOSED"):
            raise RuntimeError(f"{path_to_pgroup} is closed for writing")

        run_number = request.get("run_number", None)
        if run_number is None:
            raise RuntimeError("no run_number in request parameters")

        list_data_directories_run = glob(f"{path_to_pgroup}/run{run_number:04}*")

        if not list_data_directories_run:
            raise RuntimeError(f"no such run {run_number} in the pgroup")

        full_path = list_data_directories_run[0]
        target_directory = f"{full_path}/aux"
        if not os.path.exists(target_directory):
            try:
                os.mkdir(target_directory)
            except Exception as e:
                raise RuntimeError(f"no permission or possibility to make aux sub-directory in pgroup space (due to: {e})") from e

        group_to_copy = os.stat(target_directory).st_gid
        files_to_copy = request.get("files", [])
        error_files = []
        destination_file_path = []
        for file_to_copy in files_to_copy:
            if os.path.exists(file_to_copy):
                group_original_file = os.stat(file_to_copy).st_gid
                if group_to_copy == group_original_file:
                    try:
                        dest = shutil.copy2(file_to_copy, target_directory)
                        destination_file_path.append(dest)
                    except Exception: #TODO: also store the error?
                        error_files.append(file_to_copy)
                else:
                    error_files.append(file_to_copy)
            else:
                error_files.append(file_to_copy)

        res = {
            "status": "ok",
            "message": "user file copy finished, check error_files list",
            "error_files": error_files,
            "destination_file_path": destination_file_path
        }
        return res


    @return_status
    def get_dap_settings(self, request=None, remote_ip=None):
        if not request:
            raise RuntimeError("request parameters are empty")

        if not remote_ip:
            raise RuntimeError("can not identify from which machine request were made")

        beamline = ip_to_console(remote_ip)
        if not beamline:
            raise RuntimeError("can not determine from which console request came, rejected")

        allowed_detectors_beamline = configured_detectors_for_beamline(beamline)
        if not allowed_detectors_beamline:
            raise RuntimeError("request is made from beamline which doesnt have detectors")

        detector_name = request.get("detector_name", None)
        if not detector_name:
            raise RuntimeError("no detector name in the request")

        if detector_name not in allowed_detectors_beamline:
            raise RuntimeError(f"{detector_name} not belongs to the {beamline}")

        dap_parameters_file = f"/gpfs/photonics/swissfel/buffer/dap/config/pipeline_parameters.{detector_name}.json"
        if not os.path.exists(dap_parameters_file):
            raise RuntimeError("dap parameters file is not existing, contact support")

        dap_config = json_load(dap_parameters_file)

        return dap_config


    @return_status
    def set_dap_settings(self, request=None, remote_ip=None):
        if not request:
            raise RuntimeError("request parameters are empty")

        if not remote_ip:
            raise RuntimeError("can not identify from which machine request were made")

        beamline = ip_to_console(remote_ip)
        if not beamline:
            raise RuntimeError("can not determine from which console request came, rejected")

        allowed_detectors_beamline = configured_detectors_for_beamline(beamline)
        if not allowed_detectors_beamline:
            raise RuntimeError("request is made from beamline which doesnt have detectors")

        detector_name = request.get("detector_name", None)
        if not detector_name:
            raise RuntimeError("no detector name in the request")

        if detector_name not in allowed_detectors_beamline:
            raise RuntimeError(f"{detector_name} not belongs to the {beamline}")

        dap_parameters_file = f"/gpfs/photonics/swissfel/buffer/dap/config/pipeline_parameters.{detector_name}.json"
        if not os.path.exists(dap_parameters_file):
            raise RuntimeError("dap parameters file is not existing, contact support")

        new_parameters = request.get("parameters", {})

        dap_config = json_load(dap_parameters_file)

        changed = False
        changed_parameters = {}

        for k in new_parameters:
            if k not in dap_config or new_parameters[k] != dap_config[k]:
                old_value = dap_config.get(k, None)
                changed_parameters[k] = [old_value, new_parameters[k]]
                dap_config[k] = new_parameters[k]
                changed = True

        if changed:
            date_now = datetime.now()
            date_now_str = date_now.strftime("%d-%b-%Y_%H:%M:%S")
            backup_directory = "/gpfs/photonics/swissfel/buffer/dap/config/backup"
            if not os.path.exists(backup_directory):
                os.mkdir(backup_directory)

            shutil.copyfile(dap_parameters_file, f"{backup_directory}/pipeline_parameters.{detector_name}.json.{date_now_str}")

            try:
                json_save(dap_config, dap_parameters_file)
            except Exception as e:
                shutil.copyfile(f"{backup_directory}/pipeline_parameters.{detector_name}.json.{date_now_str}", dap_parameters_file)
                raise RuntimeError(f"problem to update dap configuration, try again and inform responsible (due to: {e})") from e

        return changed_parameters



