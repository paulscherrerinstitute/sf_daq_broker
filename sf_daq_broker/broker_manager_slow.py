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
from . import validate


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

    def get_detector_settings(self, request, remote_ip):
        validate.request(request)
        validate.remote_ip(remote_ip)

        beamline = ip_to_console(remote_ip)
        validate.beamline(beamline)

        allowed_detectors_beamline = configured_detectors_for_beamline(beamline)
        validate.allowed_detectors_beamline(allowed_detectors_beamline)

        detector_name = request.get("detector_name", None)
        validate.detector_name(detector_name)

        validate.detector_name_in_allowed_detectors_beamline(detector_name, allowed_detectors_beamline, beamline)

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


    def set_detector_settings(self, request, remote_ip):
        validate.request(request)
        validate.remote_ip(remote_ip)

        beamline = ip_to_console(remote_ip)
        validate.beamline(beamline)

        allowed_detectors_beamline = configured_detectors_for_beamline(beamline)
        validate.allowed_detectors_beamline(allowed_detectors_beamline)

        detector_name = request.get("detector_name", None)
        validate.detector_name(detector_name)

        validate.detector_name_in_allowed_detectors_beamline(detector_name, allowed_detectors_beamline, beamline)

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
            raise RuntimeError(f"could not stop detector trigger {event_code_pv_name} (due to: {e})") from e

        # allow epics to process the change
        sleep(4)

        try:
            event_code = int(event_code_pv.get())
        except Exception as e:
            raise RuntimeError(f"got unexpected value from detector trigger {event_code_pv_name}: {event_code_pv.get()} (due to: {e})") from e

        if event_code != 255:
            raise RuntimeError(f"stopping detector trigger {event_code_pv_name} failed")

        if exptime:
            detector.exptime = exptime
            _logger.info(f"setting exptime to {exptime}")

        if detector_mode:
            if detector_mode in conv_detector_settings_reverse:
                detector.settings = new_settings = conv_detector_settings_reverse[detector_mode]
                _logger.info(f"setting detector settings to {new_settings} ({detector_mode})")

        if delay:
            detector.delay = delay
            _logger.info(f"setting delay to {delay}")

        if gain_mode:
            if gain_mode in conv_detector_gain_settings_reverse:
                detector.gainmode = new_settings = conv_detector_gain_settings_reverse[gain_mode]
                _logger.info(f"setting detector gain settings to {new_settings} ({gain_mode})")

        # start triggering
        event_code_pv.put(254)
        event_code_pv.disconnect()

        return "detector settings changed successfully"


    def copy_user_files(self, request, remote_ip):
        validate.request(request)
        validate.remote_ip(remote_ip)

        beamline = ip_to_console(remote_ip)
        validate.beamline(beamline)

        allowed_detectors_beamline = configured_detectors_for_beamline(beamline)
        validate.allowed_detectors_beamline(allowed_detectors_beamline)

        validate.request_has_pgroup(request)
        pgroup = request["pgroup"]

        path_to_pgroup = f"/sf/{beamline}/data/{pgroup}/raw/"
        validate.path_to_pgroup_exists(path_to_pgroup)

        daq_directory = f"{path_to_pgroup}/run_info"
        validate.directory_exists(daq_directory)
        validate.pgroup_is_not_closed_yet(daq_directory, path_to_pgroup)

        run_number = request.get("run_number", None)
        validate.request_has_run_number(run_number)

        list_data_directories_run = glob(f"{path_to_pgroup}/run{run_number:04}*")
        validate.run_dir_exists(list_data_directories_run, run_number)

        full_path = list_data_directories_run[0]
        target_directory = f"{full_path}/aux"
        validate.directory_exists(target_directory)

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
            "message": 'copying user file(s) finished, check "error_files"',
            "error_files": error_files,
            "destination_file_path": destination_file_path
        }
        return res


    def get_dap_settings(self, request, remote_ip):
        validate.request(request)
        validate.remote_ip(remote_ip)

        beamline = ip_to_console(remote_ip)
        validate.beamline(beamline)

        allowed_detectors_beamline = configured_detectors_for_beamline(beamline)
        validate.allowed_detectors_beamline(allowed_detectors_beamline)

        detector_name = request.get("detector_name", None)
        validate.detector_name(detector_name)

        validate.detector_name_in_allowed_detectors_beamline(detector_name, allowed_detectors_beamline, beamline)

        dap_parameters_file = f"/gpfs/photonics/swissfel/buffer/dap/config/pipeline_parameters.{detector_name}.json"
        validate.dap_parameters_file_exists(dap_parameters_file)

        dap_config = json_load(dap_parameters_file)
        return dap_config


    def set_dap_settings(self, request, remote_ip):
        validate.request(request)
        validate.remote_ip(remote_ip)

        beamline = ip_to_console(remote_ip)
        validate.beamline(beamline)

        allowed_detectors_beamline = configured_detectors_for_beamline(beamline)
        validate.allowed_detectors_beamline(allowed_detectors_beamline)

        detector_name = request.get("detector_name", None)
        validate.detector_name(detector_name)

        validate.detector_name_in_allowed_detectors_beamline(detector_name, allowed_detectors_beamline, beamline)

        dap_parameters_file = f"/gpfs/photonics/swissfel/buffer/dap/config/pipeline_parameters.{detector_name}.json"
        validate.dap_parameters_file_exists(dap_parameters_file)

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
                raise RuntimeError(f"could not update DAP configuration (due to: {e})") from e

        return changed_parameters



