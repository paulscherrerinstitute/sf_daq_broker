import argparse
import os
import json
from glob import glob
import logging
from datetime import datetime

from sf_daq_broker.writer.bsread_writer import write_from_imagebuffer, write_from_databuffer_api3
from sf_daq_broker.utils import get_data_api_request
from sf_daq_broker import config

#logger = logging.getLogger("data_api3")
logger = logging.getLogger("broker_writer")
logger.setLevel("INFO")
#logger.setLevel("DEBUG")

parser = argparse.ArgumentParser()
parser.add_argument("--source", default="image", type=str, help="retrieve from image or data buffer (possible values data_api3, image, epics)")
parser.add_argument("--run_info", default=None, type=str, help="run_info json file")
args = parser.parse_args()

source = None
if args.source == "image":
    source = "image"
elif args.source == "data_api3":
    source = "data_api3"
elif args.source == "epics":
    source = "epics"

if args.run_info is None:
    print("provide run info file")
    exit(1)

if not os.path.exists(args.run_info):
    print(f'{args.run_info} is not reachable or available')
    exit(1)

with open(args.run_info, "r") as read_file:
    run_info = json.load(read_file)

if source == "image":
    if "camera_list" not in run_info:
        print("No cameras defined in run_info file")
        exit(1)
    channels = run_info.get("camera_list", [])
elif source == "data_api3":
    if "channels_list" not in run_info:
        print("No BS channels defined in run_info file")
        exit(1)
    channels = run_info.get("channels_list", [])
else:
    if "pv_list" not in run_info:
        print("No PV channels defined in run_info file")
        exit(1)
    channels = run_info.get("pv_list", [])

start_pulse_id = run_info["start_pulseid"]
stop_pulse_id = run_info["stop_pulseid"]

data_request = {}
data_request["range"] = {}
data_request["range"]["startPulseId"] = run_info["start_pulseid"]
data_request["range"]["endPulseId"] = run_info["stop_pulseid"]
data_request["channels"] = [{'name': ch, 'backend': config.IMAGE_BACKEND if ch.endswith(":FPICTURE") else config.DATA_BACKEND}
                     for ch in channels]

run_number = run_info.get("run_number", 0)
acquisition_number = run_info.get("acquisition_number", 0)

parameters = None

list_data_directories_run = glob(f'/sf/{run_info["beamline"]}/data/{run_info["pgroup"]}/raw/run{run_number:04}*')
if len(list_data_directories_run) != 1:
    print(f"Ambiguous data directries : {list_data_directories_run}")
    exit()
data_directory=list_data_directories_run[0]

if source == "image":
    output_file = f'{data_directory}/data/acq{acquisition_number:04}.CAMERAS.h5.2'

    write_from_imagebuffer(data_request, output_file, parameters)

elif source == "data_api3":
    output_file = f'{data_directory}/data/acq{acquisition_number:04}.BSDATA.h5.2'

    write_from_databuffer_api3(data_request, output_file, parameters)

else:
    output_file = f'{data_directory}/data/acq{acquisition_number:04}.PVCHANNELS.h5'

    metadata = {
                 "general/user": run_info["pgroup"],
                 "general/process": __name__,
                 "general/created": str(datetime.now()),
                 "general/instrument": run_info["beamline"]
    }

    print("post-retrieve for EPICS-BUFFER is not implemented")
