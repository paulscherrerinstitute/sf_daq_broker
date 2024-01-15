import json
import logging
import os
import string
from datetime import datetime
from glob import glob
from shutil import copyfile

import sf_daq_broker.rabbitmq.config as broker_config
from sf_daq_broker import config
from sf_daq_broker.detector.detector_config import configured_detectors_for_beamline, detector_human_names, get_streamvis_address
from sf_daq_broker.utils import get_writer_request

PEDESTAL_FRAMES=3000
# TODO : put in in config
DIR_NAME_RUN_INFO = "run_info"

_logger = logging.getLogger(__name__)

# SciCat allow following characters: letters digits _ - . % # + : = @ space(not tab)
# : is bad to have in directory name, since it's forbidden symbol in windows for file/directory names
# #, @ or space are bad to have for directory names on linux, needs a special trailing characters
# to be on safe side, also characters "=" "%" are not allowed (if there will be request from users, can enable them)
# so allowing (letters digits _ - + .)
allowed_user_tag_characters = set(string.ascii_lowercase + string.ascii_uppercase + string.digits + "_" + "-" + "+" + ".")

# not needed anymore, we replace bad characters with "_"
def check_for_allowed_user_tag_character(user_tag):
    return set(user_tag) <= allowed_user_tag_characters

def clean_user_tag(user_tag, replacement_character="_"):
    #return ''.join(char for char in user_tag if char in allowed_user_tag_characters) # don't replace but remove bad characters. In this case resulting string may be empty
    return "".join(char if char in allowed_user_tag_characters else replacement_character for char in user_tag) # replace bad characters, so if initital user_tag contained at least one character, it will not be empty (but may be "___")

def clean_last_character_user_tag(user_tag, replacement_character="_"):
    if not user_tag[-1].isalnum():
        user_tag = user_tag[:-1] + replacement_character
    return user_tag

subnet_to_beamline = { "129.129.242" : "alvra", "129.129.243" : "bernina", "129.129.244": "cristallina", "129.129.247" : "furka", "129.129.246" : "maloja" }

def ip_to_console(remote_ip):
    beamline = None
    if len(remote_ip) > 11:
        beamline = subnet_to_beamline.get(remote_ip[:11], None)
    return beamline

def get_current_run_number(daq_directory=None, file_run="LAST_RUN", increment_run_number=True):
    if daq_directory is None:
        return None

    last_run_file = daq_directory + "/" + file_run
    if not os.path.exists(last_run_file):
        run_file = open(last_run_file, "w")
        run_file.write("0")
        run_file.close()

    run_file = open(last_run_file, "r")
    last_run = int(run_file.read())
    run_file.close()

    if not increment_run_number:
        current_run = last_run
    else:
        current_run = last_run + 1

        run_file = open(last_run_file, "w")
        run_file.write(str(current_run))
        run_file.close()

    return current_run

def get_current_step_in_scan(meta_directory=None):
    if meta_directory is None:
        return None

    list = os.listdir(meta_directory)
    number_files = len(list)

    current_step = 1 if number_files==0 else number_files

    return current_step

class BrokerManager:
    REQUIRED_PARAMETERS = ["output_file"]

    def __init__(self, broker_client):
        self.broker_client = broker_client

    def close_pgroup_writing(self, request=None, remote_ip=None):

        if not request:
            return {"status" : "failed", "message" : "request parameters are empty"}

        if not remote_ip:
            return {"status" : "failed", "message" : "can not identify from which machine request were made"}

        beamline = ip_to_console(remote_ip)

        if not beamline:
            return {"status" : "failed", "message" : "can not determine from which console request came, rejected"}

        if "pgroup" not in request:
            return {"status" : "failed", "message" : "no pgroup in request parameters"}
        pgroup = request["pgroup"]

        path_to_pgroup = f"/sf/{beamline}/data/{pgroup}/raw/"
        if not os.path.exists(path_to_pgroup):
            return {"status" : "failed", "message" : f"pgroup directory {path_to_pgroup} not reachable"}

        daq_directory = f"{path_to_pgroup}{DIR_NAME_RUN_INFO}"
        if not os.path.exists(daq_directory):
            try:
                os.mkdir(daq_directory)
            except:
                return {"status" : "failed", "message" : "no permission or possibility to make run_info directory in pgroup space"}

        if os.path.exists(f"{daq_directory}/CLOSED"):
            return {"status" : "failed", "message" : f"{path_to_pgroup} is already closed for writing"}

        with open(f"{daq_directory}/CLOSED", "x") as fp:
            pass

        return {"status" : "ok", "message" : f"{pgroup} closed for writing" }


    def get_pvlist(self, remote_ip=None):

        beamline = ip_to_console(remote_ip)

        config_file = f"/home/dbe/service_configs/sf.{beamline}.epics_buffer.json"

        if not os.path.exists(config_file):
            return {"status" : f"failure, epics config file not exist for this beamline {beamline}"}

        with open(config_file) as json_file:
            config_info = json.load(json_file)

        return {"pv_list": config_info["pv_list"]}

    def set_pvlist(self, request=None, remote_ip=None):

        if not request:
            return {"status" : "failed", "message" : "request parameters are empty"}

        if not remote_ip:
            return {"status" : "failed", "message" : "can not identify from which machine request were made"}

        beamline = ip_to_console(remote_ip)

        if not beamline:
            return {"status" : "failed", "message" : "can not determine from which console request came, rejected"}

        config_file = f"/home/dbe/service_configs/sf.{beamline}.epics_buffer.json"

        if not os.path.exists(config_file):
            return {"status" : "failed", "message" : f"failure, epics config file not exist for this beamline {beamline}"}

        pv_list = request.get("pv_list", [])

        config_epics = { "pulse_id_pv": "SLAAR11-LTIM01-EVR0:RX-PULSEID", "pv_list": list(dict.fromkeys(pv_list))}

        with open(config_file, "w") as json_file:
            json.dump(config_epics, json_file, indent=2)

        date_now = datetime.now()
        date_now_str = date_now.strftime("%d-%b-%Y_%H:%M:%S")
        copyfile(config_file, f"{config_file}.{date_now_str}")

        return {"status" : "ok", "message" : config_epics["pv_list"] }

    def get_next_run_number(self, request=None, remote_ip=None, increment_run_number=True):

        if not request:
            return {"status" : "failed", "message" : "request parameters are empty"}

        if not remote_ip:
            return {"status" : "failed", "message" : "can not identify from which machine request were made"}

        beamline = ip_to_console(remote_ip)

        if not beamline:
            return {"status" : "failed", "message" : "can not determine from which console request came, rejected"}

        if "pgroup" not in request:
            return {"status" : "failed", "message" : "no pgroup in request parameters"}
        pgroup = request["pgroup"]

        path_to_pgroup = f"/sf/{beamline}/data/{pgroup}/raw/"
        if not os.path.exists(path_to_pgroup):
            return {"status" : "failed", "message" : f"pgroup directory {path_to_pgroup} not reachable"}

        daq_directory = f"{path_to_pgroup}{DIR_NAME_RUN_INFO}"
        if not os.path.exists(daq_directory):
            try:
                os.mkdir(daq_directory)
            except:
                return {"status" : "failed", "message" : "no permission or possibility to make run_info directory in pgroup space"}

        if os.path.exists(f"{daq_directory}/CLOSED"):
            return {"status" : "failed", "message" : f"{path_to_pgroup} is closed for writing"}

        next_run = get_current_run_number(daq_directory, file_run="LAST_RUN", increment_run_number=increment_run_number)

        return {"status" : "ok", "message" : str(next_run) }

    def power_on_detector(self, request=None, remote_ip=None):

        if not request:
            return {"status" : "failed", "message" : "request parameters are empty"}

        if not remote_ip:
            return {"status" : "failed", "message" : "can not identify from which machine request were made"}

        beamline = ip_to_console(remote_ip)

        if not beamline:
            return {"status" : "failed", "message" : "can not determine from which console request came, rejected"}

        allowed_detectors_beamline = configured_detectors_for_beamline(beamline)
        if len(allowed_detectors_beamline) == 0:
            return {"status" : "failed", "message" : "request is made from beamline which doesnt have detectors"}

        detector_name = request.get("detector_name", None)
        if not detector_name:
            return {"status" : "failed", "message" : "no detector name in the request"}

        if detector_name not in allowed_detectors_beamline:
            return {"status" : "failed", "message" : f"{detector_name} not belongs to the {beamline}"}

        request_power_on = {"detector_name" : detector_name,
                            "beamline" : beamline,
                            "writer_type": broker_config.TAG_POWER_ON,
                            "channels": None}

        self.broker_client.open()
        self.broker_client.send(request_power_on, broker_config.TAG_POWER_ON)
        self.broker_client.close()

        return {"status" : "ok", "message" : f"request to power on detector is sent, wait few minutes"}

    def get_list_running_detectors(self, remote_ip=None):

        beamline = ip_to_console(remote_ip)
        detectors = configured_detectors_for_beamline(beamline)

        time_now = datetime.now()
        running_detectors = []
        buffer_location = "/gpfs/photonics/swissfel/buffer"
        for detector in detectors:
            detector_buffer_file = f"{buffer_location}/{detector}/M00/LATEST"
            if os.path.exists(detector_buffer_file):
                time_file = datetime.fromtimestamp(os.path.getmtime(detector_buffer_file))
                if (time_file-time_now).total_seconds() > -30:
                    running_detectors.append(detector)

        return {"detectors" : running_detectors}


    def get_list_allowed_detectors(self, remote_ip=None):

        beamline = ip_to_console(remote_ip)
        detectors = configured_detectors_for_beamline(beamline)
        detector_names = detector_human_names()
        names = []
        for d in detector_names:
            if d in detectors:
                names.append(detector_names[d])
        detectors_visualisation_address = get_streamvis_address()
        address = []
        for d in detectors_visualisation_address:
            if d in detectors:
                address.append(detectors_visualisation_address[d])
        return {"detectors" : detectors, "names" : names, "visualisation_address" : address}

    def take_pedestal(self, request=None, remote_ip=None):

        if not request:
            return {"status" : "failed", "message" : "request parameters are empty"}

        if not remote_ip:
            return {"status" : "failed", "message" : "can not identify from which machine request were made"}

        beamline = ip_to_console(remote_ip)

        if not beamline:
            return {"status" : "failed", "message" : "can not determine from which console request came, rejected"}

        allowed_detectors_beamline = configured_detectors_for_beamline(beamline)
        if len(allowed_detectors_beamline) == 0:
            return {"status" : "failed", "message" : "request is made from beamline which doesnt have detectors"}

        rate_multiplicator = request.get("rate_multiplicator", 1)

        if "detectors" not in request:
            return {"status" : "failed", "message" : "no detectors defined"}

        detectors = list(request["detectors"].keys())

        if len(detectors) < 1:
            return {"status" : "failed", "message" : "no detectors defined"}

        for det in detectors:
            if det not in allowed_detectors_beamline:
                return {"status" : "failed", "message" : f"{det} not belongs to the {beamline}"}

        if "pgroup" not in request:
            return {"status" : "failed", "message" : "no pgroup in request parameters"}
        pgroup = request["pgroup"]

        path_to_pgroup = f"/sf/{beamline}/data/{pgroup}/raw/"
        if not os.path.exists(path_to_pgroup):
            return {"status" : "failed", "message" : f"pgroup directory {path_to_pgroup} not reachable"}

        # Force output directory name to be JF_pedestals
        request["directory_name"] = "JF_pedestals"

        full_path = path_to_pgroup+request["directory_name"]

        if not os.path.exists(full_path):
            try:
                os.makedirs(full_path)
            except:
                return {"status" : "failed", "message" : f"no permission or possibility to make directory in pgroup space {full_path}"}

        daq_directory = f"{path_to_pgroup}{DIR_NAME_RUN_INFO}"
        if not os.path.exists(daq_directory):
            try:
                os.mkdir(daq_directory)
            except:
                return {"status" : "failed", "message" : "no permission or possibility to make run_info directory in pgroup space"}

        if os.path.exists(f"{daq_directory}/CLOSED"):
            return {"status" : "failed", "message" : f"{path_to_pgroup} is closed for writing"}

        if "request_time" not in request:
            request["request_time"] = str(datetime.now())

        request_time=datetime.now()

        pedestal_name = f'{request_time.strftime("%Y%m%d_%H%M%S")}'

        run_info_directory = f"{full_path}"

        run_file_json = f"{run_info_directory}/{pedestal_name}.json"

        with open(run_file_json, "w") as request_json_file:
            json.dump(request, request_json_file, indent=2)

        pedestal_request = {"detectors": detectors,
                            "rate_multiplicator": rate_multiplicator,
                            "writer_type": broker_config.TAG_PEDESTAL,
                            "channels": None,
                            "start_pulse_id": 0,
                            "stop_pulse_id": 100,
                            "output_file": None,
                            "run_log_file": f"{run_info_directory}/{pedestal_name}.log",
                            "metadata": None,
                            "timestamp": None,
                            "run_file_json" : run_file_json,
                            "path_to_pgroup" : path_to_pgroup,
                            "run_info_directory" : run_info_directory,
                            "output_file_prefix" :f"{full_path}/{pedestal_name}",
                            "directory_name" : request.get("directory_name"),
                            "request_time" : str(request_time)
                           }
        self.broker_client.open()
        self.broker_client.send(pedestal_request, broker_config.TAG_PEDESTAL)
        self.broker_client.close()

        time_to_wait = PEDESTAL_FRAMES/100*rate_multiplicator+10

        return {"status" : "ok", "message" : f"will do a pedestal now, wait at least {time_to_wait} seconds",
                                 "run_number" : str(0),
                                 "acquisition_number": str(0),
                                 "unique_acquisition_number": str(0) }

    def retrieve(self, request=None, remote_ip=None, beamline_force=None):

        if not request:
            return {"status" : "failed", "message" : "request parameters are empty"}

        if not remote_ip:
            return {"status" : "failed", "message" : "can not identify from which machine request were made"}

        if beamline_force:
            beamline = beamline_force
        else:
            beamline = ip_to_console(remote_ip)

        if not beamline:
            return {"status" : "failed", "message" : "can not determine from which console request came, rejected"}

        if "pgroup" not in request:
            return {"status" : "failed", "message" : "no pgroup in request parameters"}
        pgroup = request["pgroup"]

        if "start_pulseid" not in request or "stop_pulseid" not in request:
            return {"status" : "failed", "message" : "no start or stop pluseid provided in request parameters"}
        try:
            request["start_pulseid"] = int(request["start_pulseid"])
            request["stop_pulseid"] = int(request["stop_pulseid"])
        except:
            return {"status" : "failed", "message" : "bad start or stop pluseid provided in request parameters"}
        start_pulse_id = request["start_pulseid"]
        stop_pulse_id  = request["stop_pulseid"]

        if (stop_pulse_id-start_pulse_id) > 60001 or (stop_pulse_id-start_pulse_id) < 0:
            return {"status" : "failed", "message" : f"number of pulse_id problem: too large or negative request"}

        rate_multiplicator = 1
        if "rate_multiplicator" in request:
            if request["rate_multiplicator"] not in [1, 2, 4, 8, 10, 20, 40, 50, 100]:
                return {"status" : "failed", "message" : "rate_multiplicator is not allowed one"}
            rate_multiplicator = request["rate_multiplicator"]

# to be sure that interesting (corresponding to beam rate) pulse_id are covered by the request call
        adjusted_start_pulse_id = start_pulse_id
        adjusted_stop_pulse_id = stop_pulse_id

        if rate_multiplicator != 1:
            if adjusted_start_pulse_id%rate_multiplicator == 0:
                adjusted_start_pulse_id -= 1

            if adjusted_stop_pulse_id%rate_multiplicator == 0:
                adjusted_stop_pulse_id += 1

        path_to_pgroup = f"/sf/{beamline}/data/{pgroup}/raw/"
        if not os.path.exists(path_to_pgroup):
            return {"status" : "failed", "message" : f"pgroup directory {path_to_pgroup} not reachable"}

        daq_directory = f"{path_to_pgroup}{DIR_NAME_RUN_INFO}"

        if not os.path.exists(daq_directory):
            try:
                os.mkdir(daq_directory)
            except:
                return {"status" : "failed", "message" : "no permission or possibility to make run_info directory in pgroup space"}

        if "run_number" not in request:
            request["run_number"] = get_current_run_number(daq_directory, file_run="LAST_RUN")
        else:
            current_known_run_number = get_current_run_number(daq_directory, file_run="LAST_RUN", increment_run_number=False)
            run_number = request.get("run_number")
            if run_number > current_known_run_number:
                return {"status" : "failed", "message" : f"requested run_number{run_number} generated not by sf-daq"}

        run_number = request.get("run_number")
        output_run_directory = f"run{run_number:04}"

        append_user_tag = request.get("append_user_tag_to_data_dir", False)
        user_tag = request.get("user_tag", None)

        if append_user_tag and user_tag is not None and len(user_tag) > 0:
            cleaned_user_tag = clean_user_tag(user_tag)
            cleaned_user_tag = cleaned_user_tag[:50] # may be this is will not be needed in future
            cleaned_user_tag = clean_last_character_user_tag(cleaned_user_tag) # replace last character if it's not digit or letter
            request["appended_directory_suffix"] = cleaned_user_tag
            output_run_directory = f"run{run_number:04}-{cleaned_user_tag}"

        list_data_directories_run = glob(f"{path_to_pgroup}/run{run_number:04}*")
        if len(list_data_directories_run) > 0:
            if f"{path_to_pgroup}{output_run_directory}" not in list_data_directories_run:
                return {"status" : "failed", "message" : f"data directory for this run {run_number:04} already exists with different tag : {list_data_directories_run}, than requested {user_tag}"}

        full_path = f"{path_to_pgroup}{output_run_directory}"

        if os.path.exists(f"{daq_directory}/CLOSED"):
            return {"status" : "failed", "message" : f"{path_to_pgroup} is closed for writing"}

        write_data = False
        if "channels_list" in request or "camera_list" in request or "pv_list" in request or "detectors" in request:
            write_data = True

        if not write_data:
            return {"status" : "pass", "message" : "everything fine but no request to write any data"}

        if "detectors" in request and type(request["detectors"]) is not dict:
            return {"status" : "failed", "message" : f'{request["detectors"]} is not dictionary'}

        detectors = []
        if "detectors" in request:
            detectors = list(request["detectors"].keys())

        if len(detectors) > 0:
            allowed_detectors_beamline = configured_detectors_for_beamline(beamline)
            if len(allowed_detectors_beamline) == 0:
                return {"status" : "failed", "message" : "request is made from beamline which doesnt have detectors"}

            for det in detectors:
                if det not in allowed_detectors_beamline:
                    return {"status" : "failed", "message" : f"{det} not belongs to the {beamline}"}


        if "channels_list" in request:
            request["channels_list"] = list(dict.fromkeys(request["channels_list"]))

        if "pv_list" in request:
            request["pv_list"] = list(dict.fromkeys(request["pv_list"]))

        if not os.path.exists(full_path):
            try:
                os.makedirs(full_path)
            except:
                return {"status" : "failed", "message" : f"no permission or possibility to make directory in pgroup space {full_path}"}

        run_info_directory =    f"{full_path}/logs"
        meta_directory =        f"{full_path}/meta"
        output_data_directory = f"{full_path}/data"

        try:
            if not os.path.exists(run_info_directory):
                os.mkdir(run_info_directory)
            if not os.path.exists(meta_directory):
                os.mkdir(meta_directory)
            if not os.path.exists(output_data_directory):
                os.mkdir(output_data_directory)
        except:
            # should not come here, directory should already exists (either made few lines above or in the previous data taking to that directory)
            return {"status" : "failed", "message" : f"no permission or possibility to make directories in pgroup space {full_path} (meta,logs,data)"}

        current_acq = get_current_step_in_scan(meta_directory)
        unique_acq = get_current_run_number(daq_directory, file_run="LAST_ARUN")

        request["beamline"]     = beamline
        request["acquisition_number"]   = current_acq
        request["request_time"] = str(datetime.now())
        request["unique_acquisition_run_number"] = unique_acq

        run_file_json = f"{meta_directory}/acq{current_acq:04}.json"

        with open(run_file_json, "w") as request_json_file:
            json.dump(request, request_json_file, indent=2)

        output_files_list = []

        metadata = {
                     "general/user": str(pgroup[1:6]),
                     "general/process": __name__,
                     "general/created": str(datetime.now()),
                     "general/instrument": beamline
        }

        output_file_prefix = f"{output_data_directory}/acq{current_acq:04}"
        if not os.path.exists(output_data_directory):
            os.mkdir(output_data_directory)

        def send_write_request(tag, channels, filename_suffix):

            if not channels:
                return

            output_file = f"{output_file_prefix}.{filename_suffix}.h5"
            output_files_list.append(output_file)

            run_log_file = f"{run_info_directory}/acq{current_acq:04}.{filename_suffix}.log"

            write_request = get_writer_request(writer_type=tag,
                                               channels=channels,
                                               output_file=output_file,
                                               metadata=metadata,
                                               start_pulse_id=adjusted_start_pulse_id,
                                               stop_pulse_id=adjusted_stop_pulse_id,
                                               run_log_file=run_log_file)

            try:
                self.broker_client.send(write_request, tag)
            except:
                log_file = open(write_request["run_log_file"], "a")
                log_file.write("Can not contact writer")
                log_file.close()
                raise

        self.broker_client.open()

        send_write_request(f"epics_{beamline}",
                           request.get("pv_list"),
                           config.OUTPUT_FILE_SUFFIX_EPICS_BUFFER)

        send_write_request(broker_config.TAG_DATA3BUFFER,
                           request.get("channels_list"),
                           config.OUTPUT_FILE_SUFFIX_DATA3_BUFFER)

        send_write_request(broker_config.TAG_IMAGEBUFFER,
                           request.get("camera_list"),
                           config.OUTPUT_FILE_SUFFIX_IMAGE_BUFFER)

        if "detectors" in request:
            request_detector = {}

            det_start_pulse_id = 0
            det_stop_pulse_id = stop_pulse_id
            for p in range(start_pulse_id, stop_pulse_id+1):
                if p%rate_multiplicator == 0:
                    det_stop_pulse_id = p
                    if det_start_pulse_id == 0:
                        det_start_pulse_id = p
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
                send_write_request(broker_config.TAG_DETECTOR_RETRIEVE,
                           request_detector,
                           detector)

        self.broker_client.close()

        each_scan_fields = ["scan_readbacks", "scan_step_info", "scan_values", "scan_readbacks_raw"]

        request_scan_info = request.get("scan_info", {"scan_name": "dummy",
                                                      "Id": ["dummy"],
                                                      "name": ["dummy"],
                                                      "offset": [0],
                                                      "conversion_factor": [1.0],
                                                      "scan_readbacks": [0],
                                                      "scan_readbacks_raw": [0],
                                                      "scan_values": [0]})
        scan_info_file = f"{meta_directory}/scan.json"
        if not os.path.exists(scan_info_file):
            scan_info = {"scan_files" : [], "pulseIds": []}
            scan_info["scan_parameters"] = {}
            for scan_key in request_scan_info:
                if scan_key not in each_scan_fields:
                    scan_info["scan_parameters"][scan_key] = request_scan_info[scan_key]
            for scan_step_field in each_scan_fields:
                scan_info[scan_step_field] = []
        else:
            with open(scan_info_file) as json_file:
                scan_info = json.load(json_file)

        for scan_step_field in each_scan_fields:
            scan_info[scan_step_field].append(request_scan_info.get(scan_step_field, []))

        scan_info["scan_files"].append(output_files_list)
        scan_info["pulseIds"].append([start_pulse_id, stop_pulse_id])

        with open(scan_info_file, "w") as json_file:
            json.dump(scan_info, json_file, indent=4)

        return {"status" : "ok", "message" : "OK",
                                 "run_number" : str(run_number),
                                 "acquisition_number": str(current_acq),
                                 "unique_acquisition_number": str(unique_acq),
                                 "files" : output_files_list }
