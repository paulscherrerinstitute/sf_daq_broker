import logging
import os
import string
from datetime import datetime
from shutil import copyfile

from sf_daq_broker import config
from sf_daq_broker.detector.utils import configured_detectors_for_beamline, detector_human_names, get_streamvis_address
from sf_daq_broker.rabbitmq import broker_config
from sf_daq_broker.utils import get_writer_request, get_beamline, json_save, json_load
from . import validate


_logger = logging.getLogger(__name__)

PEDESTAL_FRAMES = 3000
#TODO: move to config
DIR_NAME_RUN_INFO = "run_info"

# SciCat allows the following characters: letters digits _ - . % # + : = @ space (not tab)
# : may be problematic since it is a forbidden character for file/directory names under Windows
# #, @ and space may be problematic since these need a special trailing character in directory names under Linux
# to be on the safe side, the characters = % are also not allowed (but could be enabled upon user request)
# thus allowing: letters digits _ - + .
allowed_user_tag_characters = set(string.ascii_lowercase + string.ascii_uppercase + string.digits + "_" + "-" + "+" + ".")



class BrokerManager:

    def __init__(self, broker_client):
        self.broker_client = broker_client


    def close_pgroup_writing(self, request, remote_ip):
        validate.request_has(request, "pgroup")

        beamline = get_beamline(remote_ip)

        pgroup = request["pgroup"]

        path_to_pgroup = f"/sf/{beamline}/data/{pgroup}/raw/"
        validate.path_to_pgroup_exists(path_to_pgroup)

        daq_directory = f"{path_to_pgroup}{DIR_NAME_RUN_INFO}"
        validate.directory_exists(daq_directory)
        validate.pgroup_is_not_closed_yet(daq_directory, path_to_pgroup)

        with open(f"{daq_directory}/CLOSED", "x"):
            pass

        return f"{pgroup} closed for writing"


    def get_pvlist(self, request, remote_ip):
        validate.request_is_empty(request)

        beamline = get_beamline(remote_ip)

        config_file = f"/home/dbe/service_configs/sf.{beamline}.epics_buffer.json"
        validate.epics_config_file_exists(config_file, beamline)

        config_info = json_load(config_file)
        pv_list = config_info["pv_list"]

        res = {
            "status": "ok",
            "message": "successfully retrieved list of PVs",
            "pv_list": pv_list
        }
        return res


    def set_pvlist(self, request, remote_ip):
        validate.request_has(request, "pv_list")

        beamline = get_beamline(remote_ip)

        config_file = f"/home/dbe/service_configs/sf.{beamline}.epics_buffer.json"
        validate.epics_config_file_exists(config_file, beamline)

        pv_list = request["pv_list"]
        pv_list = list(dict.fromkeys(pv_list))

        config_epics = {
            "pulse_id_pv": "SLAAR11-LTIM01-EVR0:RX-PULSEID", #TODO: this should be matched to the BL
            "pv_list": pv_list
        }

        json_save(config_epics, config_file)

        date_now = datetime.now()
        date_now_str = date_now.strftime("%d-%b-%Y_%H:%M:%S")
        config_file_timestamped = f"{config_file}.{date_now_str}"
        copyfile(config_file, config_file_timestamped)

        return pv_list


    def get_last_run_number(self, request, remote_ip, increment_run_number=False):
        return self.get_next_run_number(request=request, remote_ip=remote_ip, increment_run_number=increment_run_number)


    def get_next_run_number(self, request, remote_ip, increment_run_number=True):
        validate.request_has(request, "pgroup")

        beamline = get_beamline(remote_ip)

        pgroup = request["pgroup"]

        path_to_pgroup = f"/sf/{beamline}/data/{pgroup}/raw/"
        validate.path_to_pgroup_exists(path_to_pgroup)

        daq_directory = f"{path_to_pgroup}{DIR_NAME_RUN_INFO}"
        validate.directory_exists(daq_directory)

        validate.pgroup_is_not_closed(daq_directory, path_to_pgroup)

        next_run = get_current_run_number(daq_directory, increment_run_number=increment_run_number)
        return next_run


    def power_on_detector(self, request, remote_ip):
        validate.request_has(request, "detector_name")

        beamline = get_beamline(remote_ip)

        allowed_detectors_beamline = configured_detectors_for_beamline(beamline)
        validate.allowed_detectors_beamline(allowed_detectors_beamline)

        detector_name = request["detector_name"]

        validate.detector_name_in_allowed_detectors_beamline(detector_name, allowed_detectors_beamline, beamline)

        request_power_on = {
            "detector_name": detector_name,
            "beamline": beamline,
            "writer_type": broker_config.TAG_POWER_ON,
            "channels": None
        }

        self.broker_client.open()
        self.broker_client.send(request_power_on, broker_config.TAG_POWER_ON)
        self.broker_client.close()

        return "request to power on detector sent, wait a few minutes"


    def get_running_detectors_list(self, request, remote_ip):
        validate.request_is_empty(request)

        beamline = get_beamline(remote_ip)

        allowed_detectors_beamline = configured_detectors_for_beamline(beamline)
        validate.allowed_detectors_beamline(allowed_detectors_beamline)

        time_now = datetime.now()
        running_detectors = []
        buffer_location = "/gpfs/photonics/swissfel/buffer"
        for detector in allowed_detectors_beamline:
            detector_buffer_file = f"{buffer_location}/{detector}/M00/LATEST"
            if os.path.exists(detector_buffer_file):
                time_file = datetime.fromtimestamp(os.path.getmtime(detector_buffer_file))
                if (time_file-time_now).total_seconds() > -30: #TODO: hmm?
                    running_detectors.append(detector)

        res = {
            "status": "ok",
            "message": "successfully retrieved list of running detectors",
            "detectors": running_detectors
        }
        return res


    def get_allowed_detectors_list(self, request, remote_ip):
        validate.request_is_empty(request)

        beamline = get_beamline(remote_ip)

        allowed_detectors_beamline = configured_detectors_for_beamline(beamline)
        validate.allowed_detectors_beamline(allowed_detectors_beamline)

        detectors = allowed_detectors_beamline

        detector_names = detector_human_names()
        names = []
        for k, v in detector_names.items():
            if k in detectors:
                names.append(v)

        detectors_visualisation_address = get_streamvis_address()
        address = []
        for k, v in detectors_visualisation_address.items():
            if k in detectors:
                address.append(v)

        res = {
            "status": "ok",
            "message": f"successfully retrieved list of allowed detectors for {beamline}",
            "detectors": detectors,
            "names": names,
            "visualisation_address": address
        }
        return res


    def take_pedestal(self, request, remote_ip):
        validate.request_has(request, "pgroup", "detectors")

        beamline = get_beamline(remote_ip)

        allowed_detectors_beamline = configured_detectors_for_beamline(beamline)
        validate.allowed_detectors_beamline(allowed_detectors_beamline)

        rate_multiplicator = request.get("rate_multiplicator", 1)

        detectors = list(request["detectors"])
        validate.detectors(detectors)

        validate.all_detector_names_in_allowed_detectors_beamline(detectors, allowed_detectors_beamline, beamline)

        pgroup = request["pgroup"]

        path_to_pgroup = f"/sf/{beamline}/data/{pgroup}/raw/"
        validate.path_to_pgroup_exists(path_to_pgroup)

        # Force output directory name to be JF_pedestals
        request["directory_name"] = directory_name = "JF_pedestals"

        full_path = f"{path_to_pgroup}{directory_name}"
        validate.directory_exists(full_path)

        daq_directory = f"{path_to_pgroup}{DIR_NAME_RUN_INFO}"
        validate.directory_exists(daq_directory)

        validate.pgroup_is_not_closed(daq_directory, path_to_pgroup)

        if "request_time" not in request:
            request["request_time"] = str(datetime.now())

        request_time = datetime.now() #TODO: this causes inconsistency between the json-dumped request and the file name
        pedestal_name = request_time.strftime("%Y%m%d_%H%M%S")
        run_info_directory = full_path
        run_file_json = f"{run_info_directory}/{pedestal_name}.json"

        json_save(request, run_file_json)

        pedestal_request = {
            "detectors": detectors,
            "rate_multiplicator": rate_multiplicator,
            "writer_type": broker_config.TAG_PEDESTAL,
            "channels": None,
            "start_pulse_id": 0,
            "stop_pulse_id": 100,
            "output_file": None,
            "run_log_file": f"{run_info_directory}/{pedestal_name}.log",
            "metadata": None,
            "timestamp": None,
            "run_file_json": run_file_json,
            "path_to_pgroup": path_to_pgroup,
            "run_info_directory": run_info_directory,
            "output_file_prefix": f"{full_path}/{pedestal_name}",
            "directory_name": directory_name,
            "request_time": str(request_time)
        }

        self.broker_client.open()
        self.broker_client.send(pedestal_request, broker_config.TAG_PEDESTAL)
        self.broker_client.close()

        time_to_wait = PEDESTAL_FRAMES / 100 * rate_multiplicator + 10

        res = {
            "status": "ok",
            "message": f"request to take pedestal sent, wait at least {time_to_wait} seconds",
            #TODO: are these needed?
            "run_number": str(0),
            "acquisition_number": str(0),
            "unique_acquisition_number": str(0)
        }
        return res


    def retrieve_from_buffers(self, request, remote_ip):
        validate.request_has(request, "pgroup", "start_pulseid", "stop_pulseid")

        beamline = get_beamline(remote_ip)

        pgroup = request["pgroup"]

        validate.request_has_integer_pulseids(request)

        start_pulse_id = request["start_pulseid"]
        stop_pulse_id  = request["stop_pulseid"]

        validate.allowed_pulseid_range(start_pulse_id, stop_pulse_id)

        rate_multiplicator = request.get("rate_multiplicator", 1)
        validate.rate_multiplicator(rate_multiplicator)

        # align pulse IDs to FEL rep. rate
        adjusted_start_pulse_id = start_pulse_id
        adjusted_stop_pulse_id  = stop_pulse_id

        if rate_multiplicator != 1:
            if adjusted_start_pulse_id % rate_multiplicator == 0:
                adjusted_start_pulse_id -= 1

            if adjusted_stop_pulse_id % rate_multiplicator == 0:
                adjusted_stop_pulse_id += 1

        path_to_pgroup = f"/sf/{beamline}/data/{pgroup}/raw/"
        validate.path_to_pgroup_exists(path_to_pgroup)

        daq_directory = f"{path_to_pgroup}{DIR_NAME_RUN_INFO}"
        validate.directory_exists(daq_directory)

        if "run_number" not in request:
            request["run_number"] = get_current_run_number(daq_directory)
        else:
            current_known_run_number = get_current_run_number(daq_directory, increment_run_number=False)
            run_number = request.get("run_number")
            validate.allowed_run_number(run_number, current_known_run_number)

        run_number = request.get("run_number")
        output_run_directory = f"run{run_number:04}"

        append_user_tag = request.get("append_user_tag_to_data_dir", False)
        user_tag = request.get("user_tag", None)

        if append_user_tag and user_tag is not None and len(user_tag) > 0:
            cleaned_user_tag = clean_user_tag(user_tag)
            cleaned_user_tag = cleaned_user_tag[:50]
            cleaned_user_tag = clean_last_character_user_tag(cleaned_user_tag)
            request["appended_directory_suffix"] = cleaned_user_tag
            output_run_directory = f"run{run_number:04}-{cleaned_user_tag}"

        validate.tag_matching_previous(path_to_pgroup, run_number, output_run_directory, user_tag)

        validate.pgroup_is_not_closed(daq_directory, path_to_pgroup)

        write_data = "channels_list" in request or "camera_list" in request or "pv_list" in request or "detectors" in request
        if not write_data:
            res = {
                "status": "pass",
                "message": "request did not contain any channels to be written to file"
            }
            return res

        request_detectors = request.get("detectors", {})
        validate.request_detectors_is_dict(request_detectors)

        detectors = list(request_detectors)
        if detectors:
            allowed_detectors_beamline = configured_detectors_for_beamline(beamline)
            validate.allowed_detectors_beamline(allowed_detectors_beamline)
            validate.all_detector_names_in_allowed_detectors_beamline(detectors, allowed_detectors_beamline, beamline)

        if "channels_list" in request:
            request["channels_list"] = list(dict.fromkeys(request["channels_list"]))

        if "pv_list" in request:
            request["pv_list"] = list(dict.fromkeys(request["pv_list"]))

        full_path = f"{path_to_pgroup}{output_run_directory}"
        validate.directory_exists(full_path)

        run_info_directory =    f"{full_path}/logs"
        meta_directory =        f"{full_path}/meta"
        output_data_directory = f"{full_path}/data"

        validate.directory_exists(run_info_directory)
        validate.directory_exists(meta_directory)
        validate.directory_exists(output_data_directory)

        current_acq = get_current_step_in_scan(meta_directory)
        unique_acq = get_current_run_number(daq_directory)

        request["beamline"] = beamline
        request["acquisition_number"] = current_acq
        request["request_time"] = str(datetime.now())
        request["unique_acquisition_run_number"] = unique_acq

        run_file_json = f"{meta_directory}/acq{current_acq:04}.json"
        json_save(request, run_file_json)

        metadata = {
            "general/user": str(pgroup[1:6]),
            "general/process": __name__,
            "general/created": str(datetime.now()),
            "general/instrument": beamline
        }

        output_files_list = []
        output_file_prefix = f"{output_data_directory}/acq{current_acq:04}"

        if not os.path.exists(output_data_directory):
            os.mkdir(output_data_directory)

        def send_write_request(tag, channels, filename_suffix):
            if not channels:
                return

            output_file = f"{output_file_prefix}.{filename_suffix}.h5"
            output_files_list.append(output_file)

            run_log_file = f"{run_info_directory}/acq{current_acq:04}.{filename_suffix}.log"

            write_request = get_writer_request(
                writer_type=tag,
                channels=channels,
                output_file=output_file,
                metadata=metadata,
                start_pulse_id=adjusted_start_pulse_id,
                stop_pulse_id=adjusted_stop_pulse_id,
                run_log_file=run_log_file
            )

            try:
                self.broker_client.send(write_request, tag)
            except Exception as e:
                with open(write_request["run_log_file"], "a") as log_file:
                    log_file.write(f"Cannot send request to writer (due to: {e})")
                raise

        self.broker_client.open()

        send_write_request(
            f"epics_{beamline}",
            request.get("pv_list"),
            config.OUTPUT_FILE_SUFFIX_EPICS_BUFFER
        )

        send_write_request(
            broker_config.TAG_DATA3BUFFER,
            request.get("channels_list"),
            config.OUTPUT_FILE_SUFFIX_DATA3_BUFFER
        )

        send_write_request(
            broker_config.TAG_IMAGEBUFFER,
            request.get("camera_list"),
            config.OUTPUT_FILE_SUFFIX_IMAGE_BUFFER
        )

        if "detectors" in request:
            det_start_pulse_id = 0
            det_stop_pulse_id = stop_pulse_id
            for p in range(start_pulse_id, stop_pulse_id+1):
                if p % rate_multiplicator == 0:
                    det_stop_pulse_id = p
                    if det_start_pulse_id == 0:
                        det_start_pulse_id = p

            request_detector = {}

            request_detector["det_start_pulse_id"] = det_start_pulse_id
            request_detector["det_stop_pulse_id"]  = det_stop_pulse_id

            request_detector["path_to_pgroup"]     = path_to_pgroup
            request_detector["rate_multiplicator"] = rate_multiplicator
            request_detector["run_file_json"]      = run_file_json
            request_detector["run_info_directory"] = run_info_directory
            request_detector["request_time"]       = request["request_time"]
            request_detector["directory_name"]     = output_run_directory

            request_detector["beamline"]           = beamline
            request_detector["pgroup"]             = pgroup

            if "selected_pulse_ids" in request:
                request_detector["selected_pulse_ids"] = request["selected_pulse_ids"]

            for detector in request["detectors"]:
                request_detector_send = request_detector
                request_detector_send["detector_name"] = detector
                request_detector_send["detectors"] = {}
                request_detector_send["detectors"][detector] = request["detectors"][detector]
                send_write_request(
                    broker_config.TAG_DETECTOR_RETRIEVE,
                    request_detector,
                    detector
                )

        self.broker_client.close()

        each_scan_fields = [
            "scan_readbacks",
            "scan_step_info",
            "scan_values",
            "scan_readbacks_raw"
        ]

        default_scan_info = {
            "scan_name": "dummy",
            "Id": ["dummy"],
            "name": ["dummy"],
            "offset": [0],
            "conversion_factor": [1.0],
            "scan_readbacks": [0],
            "scan_readbacks_raw": [0],
            "scan_values": [0]
        }

        request_scan_info = request.get("scan_info", default_scan_info)

        scan_info_file = f"{meta_directory}/scan.json"
        if not os.path.exists(scan_info_file):
            scan_info = {
                "scan_files": [],
                "pulseIds": []
            }
            scan_info["scan_parameters"] = {}
            for scan_key in request_scan_info:
                if scan_key not in each_scan_fields:
                    scan_info["scan_parameters"][scan_key] = request_scan_info[scan_key]
            for scan_step_field in each_scan_fields:
                scan_info[scan_step_field] = []
        else:
            scan_info = json_load(scan_info_file)

        for scan_step_field in each_scan_fields:
            scan_info[scan_step_field].append(
                request_scan_info.get(scan_step_field, [])
            )

        scan_info["scan_files"].append(output_files_list)
        scan_info["pulseIds"].append([start_pulse_id, stop_pulse_id])

        json_save(scan_info, scan_info_file)

        res = {
            "status": "ok",
            "message": "OK",
            "run_number": str(run_number),
            "acquisition_number": str(current_acq),
            "unique_acquisition_number": str(unique_acq),
            "files": output_files_list
        }
        return res





## not needed anymore, forbidden characters are replaced with "_"
#def check_for_allowed_user_tag_character(user_tag):
#    return set(user_tag) <= allowed_user_tag_characters

def clean_user_tag(user_tag, replacement_character="_"):
    ## do not replace but remove forbidden characters; resulting string may be empty
    #return "".join(char for char in user_tag if char in allowed_user_tag_characters)
    # replace forbidden characters; if initital user_tag contained at least one character, it will not be empty (it may be only underscores)
    return "".join(char if char in allowed_user_tag_characters else replacement_character for char in user_tag)

def clean_last_character_user_tag(user_tag, replacement_character="_"):
    if not user_tag[-1].isalnum():
        user_tag = user_tag[:-1] + replacement_character
    return user_tag


def get_current_run_number(daq_directory=None, file_run="LAST_RUN", increment_run_number=True):
    if daq_directory is None:
        return None

    last_run_file = daq_directory + "/" + file_run
    if not os.path.exists(last_run_file):
        with open(last_run_file, "w") as run_file:
            run_file.write("0")

    with open(last_run_file, "r") as run_file:
        last_run = int(run_file.read())

    if not increment_run_number:
        current_run = last_run
    else:
        current_run = last_run + 1

        with open(last_run_file, "w") as run_file:
            run_file.write(str(current_run))

    return current_run


def get_current_step_in_scan(meta_directory=None):
    if meta_directory is None:
        return None

    dirlist = os.listdir(meta_directory)
    number_files = len(dirlist)

    current_step = 1 if number_files == 0 else number_files
    return current_step



