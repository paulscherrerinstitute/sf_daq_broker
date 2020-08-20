from datetime import datetime
from threading import Thread

import logging
import json

import requests
from bsread.sender import Sender

from sf_daq_broker import config
from sf_daq_broker.utils import get_writer_request

import os
from subprocess import Popen

_logger = logging.getLogger(__name__)


class BrokerManager(object):
    REQUIRED_PARAMETERS = ["output_file"]

    def __init__(self, request_sender, epics_writer_url=None):

        self.request_sender   = request_sender
        self.epics_writer_url = epics_writer_url

    def retrieve(self, request=None, remote_ip=None, beamline_force=None):

        if not request:
            return {"status" : "failed", "message" : "request parameters are empty"}

        if not remote_ip:
            return {"status" : "failed", "message" : "can not identify from which machine request were made"}

        if beamline_force:
            beamline = beamline_force
        else:
            beamline = None
            if len(remote_ip) > 11:
                if remote_ip[:11] == "129.129.242":
                    beamline = "alvra"
                elif remote_ip[:11] == "129.129.243":
                    beamline = "bernina"
                elif remote_ip[:11] == "129.129.246":
                    beamline = "maloja"

        if not beamline:
            return {"status" : "failed", "message" : "can not determine from which console request came, so which beamline it's"}

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

        path_to_pgroup = f'/sf/{beamline}/data/{pgroup}/raw/'
        if not os.path.exists(path_to_pgroup):
            return {"status" : "failed", "message" : f'pgroup directory {path_to_pgroup} not reachable'}

        full_path = path_to_pgroup
        if "directory_name" in request and request["directory_name"] is not None:
            # TODO cleanup directory_name from request to remove possibility to write to another pgroup folder
            full_path = path_to_pgroup+request["directory_name"]

# TODO : put in in config            
        DIR_NAME_RUN_INFO = "run_info"
        daq_directory = f'{path_to_pgroup}{DIR_NAME_RUN_INFO}'
        if not os.path.exists(daq_directory):
            try:
                os.mkdir(daq_directory)
            except:
                return {"status" : "failed", "message" : "no permission or possibility to make run_info directory in pgroup space"}

        if os.path.exists(f'{daq_directory}/CLOSED'):
            return {"status" : "failed", "message" : f'{path_to_pgroup} is closed for writing'}

        write_data = False
        if "channels_list" in request or "camera_list" in request or "pv_list" in request or "detectors" in request:
            write_data = True

        if not write_data:
            return {"status" : "pass", "message" : "everything fine but no request to write any data"}

        if "detectors" in request and type(request["detectors"]) is not dict:
            return {"status" : "failed", "message" : f'{request["detectors"]} is not dictionary'}        

        if "channels_list" in request:
            request["channels_list"] = list(set(request["channels_list"]))
            request["channels_list"].sort()
 
        last_run_file = daq_directory + "/LAST_RUN"
        if not os.path.exists(last_run_file):
            run_file = open(last_run_file, "w")
            run_file.write("0")
            run_file.close()

        run_file = open(last_run_file, "r")
        last_run = int(run_file.read())
        run_file.close()

        current_run = last_run + 1

        run_file = open(last_run_file, "w")
        run_file.write(str(current_run))
        run_file.close()

        request["beamline"]     = beamline
        request["run_number"]   = current_run
        request["request_time"] = str(datetime.now())

        current_run_thousand = current_run//1000*1000
        run_info_directory = f'{daq_directory}/{current_run_thousand:06}' 
        if not os.path.exists(run_info_directory):
            # shouldn't fail here, since before was successful in creation of daq_directory
            os.mkdir(run_info_directory)
 
        run_file_json = f'{run_info_directory}/run_{current_run:06}.json'

        with open(run_file_json, "w") as request_json_file:
            json.dump(request, request_json_file, indent=2)

        output_files_list = []

        metadata = {
                     "general/user": str(pgroup[1:6]),
                     "general/process": __name__,
                     "general/created": str(datetime.now()),
                     "general/instrument": beamline
        }

        if not os.path.exists(full_path):
            try:
                os.makedirs(full_path)
            except:
                return {"status" : "failed", "message" : f'no permission or possibility to make directory in pgroup space {full_path}'}

        output_file_prefix = f'{full_path}/run_{current_run:06}'

        if "pv_list" in request:

            output_file_epics = output_file_prefix + config.OUTPUT_FILE_SUFFIX_EPICS
            output_files_list.append(output_file_epics)

            write_request = get_writer_request(channels=request["pv_list"],
                                               output_file=output_file_epics,
                                               metadata=metadata,
                                               start_pulse_id=adjusted_start_pulse_id,
                                               stop_pulse_id=adjusted_stop_pulse_id)

            def send_epics_request():
                try:

                    epics_writer_request = {
                                "range": json.loads(write_request["data_api_request"])["range"],
                                "parameters": json.loads(write_request["parameters"]),
                                "channels" : request["pv_list"],
                                "retrieval_url" : "https://data-api.psi.ch/sf"
                            }
                    epics_writer_request["parameters"]["output_file"] = output_file_epics
                    requests.put(url=self.epics_writer_url, json=epics_writer_request)
                except Exception as e:
                    _logger.error("Error while trying to forward the write request to the epics writer.", e)
#TODO: check if url is empty?
            Thread(target=send_epics_request).start()

        if "channels_list" in request:
            output_file_bsread = output_file_prefix + config.OUTPUT_FILE_SUFFIX_DATA_BUFFER
            output_files_list.append(output_file_bsread)

            write_request = get_writer_request(channels=request["channels_list"],
                                               output_file=output_file_bsread,
                                               metadata=metadata,
                                               start_pulse_id=adjusted_start_pulse_id,
                                               stop_pulse_id=adjusted_stop_pulse_id)

            self.request_sender.send(write_request)

        if "camera_list" in request:
            output_file_cameras = output_file_prefix + config.OUTPUT_FILE_SUFFIX_IMAGE_BUFFER
            output_files_list.append(output_file_cameras)

            write_request = get_writer_request(channels=request["camera_list"],
                                               output_File=output_file_cameras,
                                               metadata=metadata,
                                               start_pulse_id=adjusted_start_pulse_id,
                                               stop_pulse_id=adjusted_stop_pulse_id)
            self.request_sender.send(write_request)

        if "detectors" in request:
            for detector in request["detectors"]:
                output_file_detector = f'{full_path}/run_{current_run:06}.{detector}.h5'
                output_files_list.append(output_file_detector)
                det_start_pulse_id = 0
                det_stop_pulse_id = stop_pulse_id

                det_conversion  = request["detectors"][detector].get("adc_to_energy", False)
                det_compression = request["detectors"][detector].get("compression", False)
                det_export = 0
                if det_conversion or det_compression:
                    det_export = 1

                raw_file_name = output_file_detector 
                if det_export == 1:
                    raw_file_name = f'{path_to_pgroup}/RAW_DATA/'
                    if "directory_name" in request and request["directory_name"] is not None:
                        raw_file_name = raw_file_name + request["directory_name"]
                    raw_file_name = f'{raw_file_name}/run_{current_run:06}.{detector}.h5'

                for p in range(start_pulse_id, stop_pulse_id+1):
                    if p%rate_multiplicator == 0:
                        det_stop_pulse_id = p
                        if det_start_pulse_id == 0:
                            det_start_pulse_id = p
                retrieve_command=f'/home/dbe/git/sf_daq_buffer/scripts/retrieve_detector_data.sh {detector} {det_start_pulse_id} {det_stop_pulse_id} {output_file_detector} {rate_multiplicator} {det_export} {run_file_json} {raw_file_name}'
                process_log_file=open(f'{run_info_directory}/run_{current_run:06}.{detector}.log','w')
                _logger.info("Starting detector retrieve command %s " % retrieve_command)
                process=Popen(retrieve_command, shell=True, stdout=process_log_file, stderr=process_log_file)
                process_log_file.close()

        if "scan_info" in request:
            request_scan_info = request["scan_info"]
            if "scan_name" in request_scan_info:
                scan_name = request_scan_info["scan_name"]
                scan_dir = path_to_pgroup+"/scan_info"
                if not os.path.exists(scan_dir):
                    os.makedirs(scan_dir)
                scan_info_file = scan_dir+"/"+scan_name+".json"
                if not os.path.exists(scan_info_file):
                    scan_info = {"scan_files" : [], "scan_parameters" : {"Id" : request_scan_info.get("motors_pv_name"), "name": request_scan_info.get("motors_name"), "offset": request_scan_info.get("motors_offset"), "conversion_factor": request_scan_info.get("motors_coefficient")}, "scan_readbacks": [], "scan_step_info": [], "scan_values": [], "scan_readbacks_raw": [], "pulseIds": []} 
                else:
                    with open(scan_info_file) as json_file:
                        scan_info = json.load(json_file)
                scan_info["scan_readbacks"].append(request_scan_info.get("motors_readback_value",[]))
                scan_info["scan_values"].append(request_scan_info.get("motors_value",[]))
                scan_info["scan_step_info"].append(request_scan_info.get("step_info"))
                scan_info["scan_readbacks_raw"].append(request_scan_info.get("motors_readback_raw",[]))

                scan_info["scan_files"].append(output_files_list)
                scan_info["pulseIds"].append([start_pulse_id, stop_pulse_id])

                with open(scan_info_file, 'w') as json_file:
                    json.dump(scan_info, json_file, indent=4)

        return {"status" : "ok", "message" : str(current_run) }
