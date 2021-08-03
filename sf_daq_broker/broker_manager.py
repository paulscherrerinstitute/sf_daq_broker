from datetime import datetime
import logging
import json
from sf_daq_broker import config
import sf_daq_broker.rabbitmq.config as broker_config
from sf_daq_broker.utils import get_writer_request

import os
from subprocess import Popen

from threading import Thread
from time import sleep

PEDESTAL_FRAMES=5000

_logger = logging.getLogger(__name__)

allowed_detectors_beamline = { "alvra" : [ "JF02T09V02", "JF06T08V02", "JF06T32V02", "JF08T01V01", "JF09T01V01", "JF10T01V01"],
                               "bernina" : [ "JF01T03V01", "JF03T01V02", "JF04T01V01", "JF05T01V01", "JF07T32V01", "JF07T03V01", "JF13T01V01", "JF14T01V01"],
                               "furka" : [],
                               "maloja" : [ "JF15T08V01"]
                             }

def ip_to_console(remote_ip):
    beamline = None
    if len(remote_ip) > 11:
        if remote_ip[:11] == "129.129.242":
            beamline = "alvra"
        elif remote_ip[:11] == "129.129.243":
            beamline = "bernina"
        elif remote_ip[:11] == "129.129.247":
            beamline = "furka"
        elif remote_ip[:11] == "129.129.246":
            beamline = "maloja"
    return beamline

class BrokerManager(object):
    REQUIRED_PARAMETERS = ["output_file"]

    def __init__(self, broker_client):
        self.broker_client = broker_client

    def get_list_running_detectors(self, remote_ip=None):

        beamline = ip_to_console(remote_ip)
        detectors = allowed_detectors_beamline[beamline] if beamline else []

        time_now = datetime.now()   
        running_detectors = []
        buffer_location = "/gpfs/photonics/swissfel/buffer"
        for detector in detectors:
            detector_buffer_file = f'{buffer_location}/{detector}/M00/LATEST'
            if os.path.exists(detector_buffer_file):
                time_file = datetime.fromtimestamp(os.path.getmtime(detector_buffer_file))
                if (time_file-time_now).total_seconds() > -30:
                    running_detectors.append(detector)
 
        return {"detectors" : running_detectors}


    def get_list_allowed_detectors(self, remote_ip=None):

        beamline = ip_to_console(remote_ip)
        detectors = allowed_detectors_beamline[beamline] if beamline else []
        return {"detectors" : detectors}  

    def take_pedestal(self, request=None, remote_ip=None):

        if not request:
            return {"status" : "failed", "message" : "request parameters are empty"}

        if not remote_ip:
            return {"status" : "failed", "message" : "can not identify from which machine request were made"}

        beamline = ip_to_console(remote_ip)

        if not beamline:
            return {"status" : "failed", "message" : "can not determine from which console request came, rejected"}

        if beamline not in allowed_detectors_beamline:
            return {"status" : "failed", "message" : "request is made from beamline which doesnt have detectors"}

        if "start_pulseid" not in request:
            return {"status" : "failed", "message" : "no start pluseid provided in request parameters"}

        rate_multiplicator = request.get("rate_multiplicator", 1)

        if "detectors" not in request:
            return {"status" : "failed", "message" : "no detectors defined"}

        detectors = list(request["detectors"].keys())

        if len(detectors) < 1:
            return {"status" : "failed", "message" : "no detectors defined"}

        for det in detectors:
            if det not in allowed_detectors_beamline[beamline]:
                return {"status" : "failed", "message" : f"{det} not belongs to the {beamline}"}

        stop_pulseid = int(request["start_pulseid"])+PEDESTAL_FRAMES*rate_multiplicator
        pedestal_request = {"detectors": detectors, 
                            "rate_multiplicator": rate_multiplicator,
                            "writer_type": broker_config.TAG_PEDESTAL, 
                            "channels": None, 
                            "start_pulse_id": request["start_pulseid"],
                            "stop_pulse_id": stop_pulseid,
                            "output_file": None,
                            "run_log_file": None,
                            "metadata": None,
                            "timestamp": None
                           }
        self.broker_client.open()
        self.broker_client.send(pedestal_request, broker_config.TAG_PEDESTAL)
        self.broker_client.close()

        time_to_wait = PEDESTAL_FRAMES/100*rate_multiplicator+10
        return {"status" : "ok", "message" : f"will do a pedestal now, wait at least {time_to_wait} seconds", "stop_pulseid": stop_pulseid}


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

        if "directory_name" in request and request["directory_name"] is not None:
            # happened already that directory name were made with spaces, which make problem to propagate to linux scripts
            request["directory_name"] = request["directory_name"].replace(" ","_")
            # remove possibility to reffer to directory name with ".." (potentially allowing to write to another pgroup)
            request["directory_name"] = request["directory_name"].replace("..","_")

        full_path = path_to_pgroup
        if "directory_name" in request and request["directory_name"] is not None:
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

        detectors = []
        if "detectors" in request:
            detectors = list(request["detectors"].keys())

        if len(detectors) > 0:
            if beamline not in allowed_detectors_beamline:
                return {"status" : "failed", "message" : "request is made from beamline which doesnt have detectors"}

            for det in detectors:
                if det not in allowed_detectors_beamline[beamline]:
                    return {"status" : "failed", "message" : f"{det} not belongs to the {beamline}"}


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

        def send_write_request(tag, channels, filename_suffix):

            if not channels:
                return

            output_file = f'{output_file_prefix}.{filename_suffix}.h5'
            output_files_list.append(output_file)

            run_log_file = f'{run_info_directory}/run_{current_run:06}.{filename_suffix}.log'

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

        send_write_request(broker_config.TAG_EPICS,
                           request.get("pv_list"),
                           config.OUTPUT_FILE_SUFFIX_EPICS)

#        send_write_request(broker_config.TAG_DATABUFFER,
#                           request.get("channels_list"),
#                           config.OUTPUT_FILE_SUFFIX_DATA_BUFFER)

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
            request_detector["current_run"]        = current_run
            request_detector["run_info_directory"] = run_info_directory
            request_detector["request_time"]       = request["request_time"]
            if "directory_name" in request:
                request_detector["directory_name"] = request["directory_name"]

            for detector in request["detectors"]:
                request_detector_send = request_detector
                request_detector_send["detector_name"] = detector
                request_detector_send["detectors"] = {}
                request_detector_send["detectors"][detector] = request["detectors"][detector]
                send_write_request(broker_config.TAG_DETECTOR_RETRIEVE,
                           request_detector,
                           detector)

        self.broker_client.close()

        if "scan_info" in request:
            request_scan_info = request["scan_info"]
            if "scan_name" in request_scan_info:
                each_scan_fields = ["scan_readbacks", "scan_step_info", "scan_values", "scan_readbacks_raw"]
                scan_name = request_scan_info["scan_name"]
                scan_dir = path_to_pgroup+"/scan_info"
                if not os.path.exists(scan_dir):
                    os.makedirs(scan_dir)
                scan_info_file = scan_dir+"/"+scan_name+".json"
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

                with open(scan_info_file, 'w') as json_file:
                    json.dump(scan_info, json_file, indent=4)

        return {"status" : "ok", "message" : str(current_run) }
