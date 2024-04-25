import logging
import os
import shutil
from datetime import datetime
from glob import glob
from time import sleep

import epics
from slsdet import Jungfrau, gainMode
from slsdet.enums import detectorSettings

from sf_daq_broker.detector.jfctrl import JFCtrl
from sf_daq_broker.detector.utils import get_configured_detectors
from sf_daq_broker.detector.power_on_detector import BEAMLINE_EVENT_CODE
from sf_daq_broker.utils import get_beamline, json_save, json_load, dueto
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

    def get_jfctrl_monitor(self, request, remote_ip):
        validate.request_has(request, "detector_name")

        beamline = get_beamline(remote_ip)
        allowed_detectors_beamline = get_configured_detectors(beamline)

        detector_name = request["detector_name"]

        validate.detector_name_in_allowed_detectors_beamline(detector_name, allowed_detectors_beamline, beamline)

        detector_number = int(detector_name[2:4])
        jfctrl = JFCtrl(detector_number)

        parameters = jfctrl.get_monitor()

        res = {
            "status": "ok",
            "message": f"successfully retrieved JFCtrl monitor parameters from {detector_name}",
            "parameters": parameters
        }
        return res


    def get_detector_temperatures(self, request, remote_ip):
        validate.request_has(request, "detector_name")

        beamline = get_beamline(remote_ip)
        allowed_detectors_beamline = get_configured_detectors(beamline)

        detector_name = request["detector_name"]

        validate.detector_name_in_allowed_detectors_beamline(detector_name, allowed_detectors_beamline, beamline)

        detector_number = int(detector_name[2:4])
        detector = Jungfrau(detector_number)

        temperatures = {t.name: detector.getTemperature(t) for t in detector.getTemperatureList()}
        temperatures["TEMPERATURE_THRESHOLDS"] = detector.getThresholdTemperature()

        res = {
            "status": "ok",
            "message": f"successfully retrieved temperatures from {detector_name}",
            "temperatures": temperatures
        }
        return res


    def get_detector_settings(self, request, remote_ip):
        validate.request_has(request, "detector_name")

        beamline = get_beamline(remote_ip)
        allowed_detectors_beamline = get_configured_detectors(beamline)

        detector_name = request["detector_name"]

        validate.detector_name_in_allowed_detectors_beamline(detector_name, allowed_detectors_beamline, beamline)

        detector_number = int(detector_name[2:4])
        detector = Jungfrau(detector_number)

        exptime = detector.exptime
        detector_mode = conv_detector_settings.get(detector.settings, "unknown")
        delay = detector.delay
        gain_mode = conv_detector_gain_settings.get(detector.gainmode, "unknown")

        parameters = {
            "exptime": exptime,
            "detector_mode": detector_mode,
            "delay": delay,
            "gain_mode": gain_mode
        }

        res = {
            "status": "ok",
            "message": f"successfully retrieved detector settings from {detector_name}",
            "parameters": parameters
        }
        return res


    def set_detector_settings(self, request, remote_ip):
        validate.request_has(request, "detector_name", "parameters")

        beamline = get_beamline(remote_ip)
        allowed_detectors_beamline = get_configured_detectors(beamline)

        detector_name = request["detector_name"]

        validate.detector_name_in_allowed_detectors_beamline(detector_name, allowed_detectors_beamline, beamline)

        detector_number = int(detector_name[2:4])
        detector = Jungfrau(detector_number)

        parameters = request["parameters"]

        delay         = parameters.get("delay")
        detector_mode = parameters.get("detector_mode")
        exptime       = parameters.get("exptime")
        gain_mode     = parameters.get("gain_mode")

        gainmode = conv_detector_gain_settings_reverse.get(gain_mode)
        settings = conv_detector_settings_reverse.get(detector_mode)

        new_parameters = {
            "delay": delay,
            "exptime": exptime,
            "gainmode": gainmode,
            "settings": settings
        }

        new_parameters = {k: v for k, v in new_parameters.items() if v is not None}

        event_code_pv_name = BEAMLINE_EVENT_CODE[beamline]
        event_code_pv = epics.PV(event_code_pv_name)

        # stop triggering of the beamline detectors
        try:
            event_code_pv.put(255)
        except Exception as e:
            raise RuntimeError(f"could not stop detector trigger {event_code_pv_name} {dueto(e)}") from e

        # allow epics to process the change
        sleep(4)

        try:
            event_code = int(event_code_pv.get())
        except Exception as e:
            raise RuntimeError(f"got unexpected value from detector trigger {event_code_pv_name}: {event_code_pv.get()} {dueto(e)}") from e

        if event_code != 255:
            raise RuntimeError(f"stopping detector trigger {event_code_pv_name} failed")

        changed_parameters = {}
        for name, new_value in new_parameters.items():
            old_value = getattr(detector, name)
            if old_value == new_value:
                continue
            changed_parameters[name] = (old_value, new_value)
            setattr(detector, name, new_value)
            _logger.info(f'changed parameter "{name}" from {old_value} to {new_value}')

        # start triggering
        event_code_pv.put(254)
        event_code_pv.disconnect()

        res = {
            "status": "ok",
            "message": f"successfully changed detector settings of {detector_name}",
            "changed_parameters": changed_parameters
        }
        return res


    def copy_user_files(self, request, remote_ip):
        validate.request_has(request, "pgroup", "run_number")

        beamline = get_beamline(remote_ip)

        pgroup = request["pgroup"]

        path_to_pgroup = f"/sf/{beamline}/data/{pgroup}/raw/"
        validate.path_to_pgroup_exists(path_to_pgroup)

        daq_directory = f"{path_to_pgroup}/run_info"
        validate.directory_exists(daq_directory)
        validate.pgroup_is_not_closed_yet(daq_directory, path_to_pgroup)

        run_number = request["run_number"]

        list_data_directories_run = glob(f"{path_to_pgroup}/run{run_number:04}*")
        validate.run_dir_exists(list_data_directories_run, run_number)

        full_path = list_data_directories_run[0]
        target_directory = f"{full_path}/aux"
        validate.directory_exists(target_directory)
        target_group = os.stat(target_directory).st_gid

        files_to_copy = request.get("files", [])
        files_to_copy = sorted(set(files_to_copy))

        error_files = {}
        destination_files = {}

        for file_to_copy in files_to_copy:
            if not os.path.exists(file_to_copy):
                error_files[file_to_copy] = f'file "{file_to_copy}" does not exist'
                continue

            source_group = os.stat(file_to_copy).st_gid
            if source_group != target_group:
                error_files[file_to_copy] = f'group ID mismatch for file "{file_to_copy}": source {source_group} vs. target {target_group}'
                continue

            try:
                dest = shutil.copy2(file_to_copy, target_directory)
            except Exception as e:
                error_files[file_to_copy] = str(e)
            else:
                destination_files[file_to_copy] = dest

        if error_files:
            status = "error"
            message = 'copying user file(s) finished with errors, check "error_files"'
        else:
            status = "ok"
            message = "copying user file(s) finished successfully"

        res = {
            "status": status,
            "message": message,
            "error_files": error_files,
            "destination_files": destination_files
        }
        return res


    def get_dap_settings(self, request, remote_ip):
        validate.request_has(request, "detector_name")

        beamline = get_beamline(remote_ip)
        allowed_detectors_beamline = get_configured_detectors(beamline)

        detector_name = request["detector_name"]

        validate.detector_name_in_allowed_detectors_beamline(detector_name, allowed_detectors_beamline, beamline)

        dap_parameters_file = f"/gpfs/photonics/swissfel/buffer/dap/config/pipeline_parameters.{detector_name}.json"
        validate.dap_parameters_file_exists(dap_parameters_file)

        parameters = json_load(dap_parameters_file)

        res = {
            "status": "ok",
            "message": f"successfully retrieved DAP settings for {detector_name}",
            "parameters": parameters
        }
        return res


    def set_dap_settings(self, request, remote_ip):
        validate.request_has(request, "detector_name", "parameters")

        beamline = get_beamline(remote_ip)
        allowed_detectors_beamline = get_configured_detectors(beamline)

        detector_name = request["detector_name"]

        validate.detector_name_in_allowed_detectors_beamline(detector_name, allowed_detectors_beamline, beamline)

        dap_parameters_file = f"/gpfs/photonics/swissfel/buffer/dap/config/pipeline_parameters.{detector_name}.json"
        validate.dap_parameters_file_exists(dap_parameters_file)

        new_parameters = request["parameters"]

        dap_config = json_load(dap_parameters_file)

        changed_parameters = {}
        for name, new_value in new_parameters.items():
            old_value = dap_config.get(name, None)
            if old_value == new_value:
                continue
            changed_parameters[name] = (old_value, new_value)
            dap_config[name] = new_value

        if changed_parameters:
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
                raise RuntimeError(f"could not update DAP configuration {dueto(e)}") from e

        res = {
            "status": "ok",
            "message": f"successfully changed DAP settings for {detector_name}",
            "changed_parameters": changed_parameters
        }
        return res


    def get_jfstats(self, request, remote_ip):
        """
        This is a special endpoint with shorter naming to ease parsing this from an epics IOC
        """
        validate.request_has(request, "det")

        request["detector_name"] = request.pop("det")

        res1 = self.get_detector_temperatures(request, remote_ip)

        try:
            res2 = self.get_jfctrl_monitor(request, remote_ip)
        except ValueError:
            return res1

        temperatures = res1["temperatures"]
        parameters   = res2["parameters"]

        res = {
            "status": "ok",
            "message": f"successfully retrieved JFCtrl monitor parameters and temperatures from {detector_name}",
            "parameters": parameters,
            "temperatures": temperatures
        }
        return res



