import argparse
import json

import requests

broker_address = "http://sf-daq:10002"
TIMEOUT_DAQ = 10

def run():

    parser = argparse.ArgumentParser(description="simple daq client example")

    parser.add_argument("-p", "--pgroup", help="pgroup, example p12345", default="p18493")

    parser.add_argument("-c", "--channels_file", help="TXT file with list channels", default=None)

    parser.add_argument("-e", "--epics_file", help="TXT file with list of epics channels to save", default=None)

    parser.add_argument("-f", "--file_detectors", help="JSON file with the detector list", default=None)

    parser.add_argument("-r", "--rate_multiplicator", type=int, help="rate multiplicator (1(default): 100Hz, 2: 50Hz,)", default=1)

    parser.add_argument("-s", "--scan_step_file", help="JSON file with the scan step information", default=None)

    parser.add_argument("--start_pulseid", type=int, help="start pulseid", default=None)
    parser.add_argument("--stop_pulseid", type=int, help="stop pulseid", default=None)

    args = parser.parse_args()

    retrieve_data_from_buffer_files(pgroup=args.pgroup,
                              channels_file=args.channels_file, epics_file=args.epics_file,
                              detectors_file=args.file_detectors,
                              start_pulseid=args.start_pulseid, stop_pulseid=args.stop_pulseid,
                              rate_multiplicator=args.rate_multiplicator,
                              scan_step_info_file=args.scan_step_file)

def retrieve_data_from_buffer_files(pgroup=None,
                              channels_file=None, epics_file=None,
                              detectors_file=None,
                              start_pulseid=None, stop_pulseid=None,
                              rate_multiplicator=1,
                              scan_step_info_file=None):

    camera_channels = []
    bsread_channels = []

    channels = []
    if channels_file is not None:
        with open(channels_file) as input_file:
            file_lines = input_file.readlines()
            channels = [channel.strip() for channel in file_lines
                        if not channel.strip().startswith("#") and channel.strip()]

    for channel in channels:
        if channel.endswith(":FPICTURE"):
            camera_channels.append(channel)
        else:
            bsread_channels.append(channel)

    epics_channels = []
    if epics_file is not None:
        with open(epics_file) as input_file:
            file_lines = input_file.readlines()
            epics_channels = [channel.strip() for channel in file_lines
                        if not channel.strip().startswith("#") and channel.strip()]

    detectors = None
    if detectors_file is not None:
        try:
            with open(detectors_file) as json_file:
                detectors = json.load(json_file)
        except:
            print("Cannot read provided detector file, may be not json?")
            return None

    scan_step_info = None
    if scan_step_info_file is not None:
        try:
            with open(scan_step_info_file) as json_file:
                scan_step_info = json.load(json_file)
        except:
            print("Cannot read provided scan step info file, may be not json?")
            return None


    run_number = retrieve_data_from_buffer(pgroup=pgroup,
                                     camera_channels=camera_channels, bsread_channels=bsread_channels,
                                     epics_channels=epics_channels,
                                     detectors=detectors,
                                     start_pulseid=start_pulseid, stop_pulseid=stop_pulseid,
                                     rate_multiplicator=rate_multiplicator,
                                     scan_step_info=scan_step_info)
    return run_number

def retrieve_data_from_buffer(pgroup=None,
                              camera_channels=[], bsread_channels=[], epics_channels=[],
                              detectors=None,
                              start_pulseid=None, stop_pulseid=None,
                              rate_multiplicator=1,
                              scan_step_info=None):

    if pgroup is None:
        raise NameError("Provide pgroup")

    if start_pulseid is None or stop_pulseid is None:
        raise NameError("Provide stop/start pulseid")

    parameters = {}
    parameters["pgroup"]   = pgroup

    parameters["start_pulseid"] = start_pulseid
    parameters["stop_pulseid"]  = stop_pulseid

    parameters["rate_multiplicator"] = rate_multiplicator

    if len(bsread_channels) > 0:
        parameters["channels_list"] = bsread_channels

    if len(camera_channels) > 0:
        parameters["camera_list"] = camera_channels

    if len(epics_channels) > 0:
        parameters["pv_list"] = epics_channels

    if detectors is not None:
        parameters["detectors"] = detectors

    if scan_step_info is not None:
        parameters["scan_info"] = scan_step_info

    try:
        r = requests.post(f"{broker_address}/retrieve_from_buffers",json=parameters, timeout=TIMEOUT_DAQ)
    except:
        raise NameError("Cant connect to daq")

    run_number = None
    responce = r.json()
    if "status" in responce:
        if responce["status"] == "ok":
            message = responce.get("message", None)
            run_number = responce.get("run_number", None)
            if run_number is not None:
                run_number = int(run_number)
                run_number_print = f"{run_number:04}"
            else:
                run_number_print = None
            acq_number = responce.get("acquisition_number", None)
            unq_acq_number = responce.get("unique_acquisition_number", None)
            files_daq = responce.get("files", [])
            print(f"success: {message=} {run_number=} {acq_number=} {unq_acq_number=}")
            print(f" these files to expect in raw/{pgroup}/run{run_number_print}/data/ directory : {files_daq}")
        else:
            message = responce.get("message", None)
            print(f" Error, reason : {message=}")
            print(f"    whole responce : {responce=}")
    else:
        print("Bad responce from request")

    return run_number

if __name__ == "__main__":
    run()

