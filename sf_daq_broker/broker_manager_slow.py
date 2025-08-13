import logging
import os
import shutil
from datetime import datetime
from glob import glob

from sf_daq_broker.detector.jfctrl import JFCtrl
from sf_daq_broker.detector.detector import Detector
from sf_daq_broker.detector.trigger import Trigger
from sf_daq_broker.detector.utils import get_configured_detectors
from sf_daq_broker.utils import get_beamline, json_save, json_load, dueto
from . import validate


_logger = logging.getLogger(__name__)


PARAMETER_NAMES = [
    "delay",
    "detector_mode",
    "exptime",
    "gain_mode"
]



class DetectorManager:

    def get_jfctrl_monitor(self, request, remote_ip):
        detector_name = get_validated_detector_name(request, remote_ip)

        detector_number = int(detector_name[2:4])
        jfctrl = JFCtrl(detector_number)

        parameters = jfctrl.get_monitor()

        res = {
            "status": "ok",
            "message": f"successfully retrieved JFCtrl monitor parameters from {detector_name}",
            "parameters": parameters
        }
        return res


    def get_detector_pings(self, request, remote_ip):
        detector_name = get_validated_detector_name(request, remote_ip)

        detector = Detector(detector_name)

        res = {
            "status": "ok",
            "message": f"successfully retrieved pings of {detector_name}",
            "pings": detector.ping()
        }
        return res


    def get_detector_status(self, request, remote_ip):
        detector_name = get_validated_detector_name(request, remote_ip)

        detector = Detector(detector_name)

        res = {
            "status": "ok",
            "message": f"successfully retrieved status from {detector_name}",
            "detector_status": detector.status
        }
        return res


    def get_detector_temperatures(self, request, remote_ip):
        detector_name = get_validated_detector_name(request, remote_ip)

        detector = Detector(detector_name)
        temperatures = detector.get_temperatures()

        res = {
            "status": "ok",
            "message": f"successfully retrieved temperatures from {detector_name}",
            "temperatures": temperatures
        }
        return res


    def get_detector_settings(self, request, remote_ip):
        detector_name = get_validated_detector_name(request, remote_ip)

        detector = Detector(detector_name)

        parameters = {n: getattr(detector, n) for n in PARAMETER_NAMES}

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

        detector = Detector(detector_name)

        parameters = request["parameters"]

        new_parameters = {n: parameters.get(n) for n in PARAMETER_NAMES}

        trigger = Trigger(beamline)
        trigger.stop()

        changed_parameters = {}
        for name, new_value in new_parameters.items():
            if new_value is None:
                continue
            old_value = getattr(detector, name)
            if old_value == new_value:
                continue
            changed_parameters[name] = (old_value, new_value)
            setattr(detector, name, new_value)
            _logger.info(f'changed parameter "{name}" from "{old_value}" to "{new_value}"')

        trigger.start()

        res = {
            "status": "ok",
            "message": f"successfully changed detector settings of {detector_name}",
            "changed_parameters": changed_parameters
        }
        return res


    def power_on_modules(self, request, remote_ip):
        return self._set_power_modules("on", request, remote_ip)

    def power_off_modules(self, request, remote_ip):
        return self._set_power_modules("off", request, remote_ip)

    def _set_power_modules(self, target_state, request, remote_ip):
        validate.request_has(request, "detector_name", "modules")

        beamline = get_beamline(remote_ip)
        allowed_detectors_beamline = get_configured_detectors(beamline)

        detector_name = request["detector_name"]
        validate.detector_name_in_allowed_detectors_beamline(detector_name, allowed_detectors_beamline, beamline)

        detector = Detector(detector_name)

        modules = request["modules"]

        number_modules = detector.cfg.get_number_modules()

        validate.allowed_detector_modules(detector_name, modules, number_modules)

        if target_state == "on":
            detector.power_on_modules(modules)
        elif target_state == "off":
            detector.power_off_modules(modules)
        else:
            raise ValueError(f'detector modules power state can either be "on" or "off", but requested is: {target_state}')

        res = {
            "status": "ok",
            "message": f"successfully powered {target_state} modules {modules} of {detector_name}"
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
            "destination_files": destination_files,
            "error_files": error_files
        }
        return res


    def get_dap_settings(self, request, remote_ip):
        detector_name = get_validated_detector_name(request, remote_ip)

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

        request["detector_name"] = detector = request.pop("det")

        writing = get_writing_state(detector)

        res1 = self.get_detector_temperatures(request, remote_ip)

        try:
            res2 = self.get_jfctrl_monitor(request, remote_ip)
        except ValueError:
            return res1

        temperatures = res1["temperatures"]
        parameters   = res2["parameters"]

        res = {
            "status": "ok",
            "message": f"successfully retrieved JFCtrl monitor parameters and temperatures from {detector}",
            "parameters": parameters,
            "temperatures": temperatures,
            "writing": writing
        }
        return res



def get_writing_state(detector):
    detector_buffer_file = f"/gpfs/photonics/swissfel/buffer/{detector}/M00/LATEST"
    if not os.path.exists(detector_buffer_file):
        return False

    time_file = datetime.fromtimestamp(os.path.getmtime(detector_buffer_file))
    time_now = datetime.now()
    delta_time = time_now - time_file
    writing = (delta_time.total_seconds() < 30)
    return writing



def get_validated_detector_name(request, remote_ip):
    validate.request_has(request, "detector_name")

    beamline = get_beamline(remote_ip)
    allowed_detectors_beamline = get_configured_detectors(beamline)

    detector_name = request["detector_name"]
    validate.detector_name_in_allowed_detectors_beamline(detector_name, allowed_detectors_beamline, beamline)

    return detector_name



