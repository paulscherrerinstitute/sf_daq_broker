import argparse
import logging
import os
from glob import glob

from sf_daq_broker import config
from sf_daq_broker.writer.bsread_writer import write_from_databuffer_api3, write_from_imagebuffer
from sf_daq_broker.utils import json_load


_logger = logging.getLogger("broker_writer") #TODO: or "data_api3" ?


ALLOWED_SOURCES = [
    "image",
    "data_api3",
#    "epics"
]

PRINTABLE_ALLOWED_SOURCES = ", ".join(sorted(ALLOWED_SOURCES))

ENTRY_NAMES = {
    "image":     "camera_list",
    "data_api3": "channels_list",
#    "epics":     "pv_list"
}

FTYPES = {
    "image":     "CAMERAS",
    "data_api3": "BSDATA",
#    "epics":     "PVCHANNELS"
}

WRITERS = {
    "image":     write_from_imagebuffer,
    "data_api3": write_from_databuffer_api3
}



def run():
    parser = argparse.ArgumentParser(description="post retrieve")

    parser.add_argument("run_info", help="run_info json file")
    parser.add_argument("--source", "-s", default="image", choices=ALLOWED_SOURCES, help=f"retrieve from image or data buffer (possible values: {PRINTABLE_ALLOWED_SOURCES})")
    parser.add_argument("--log_level", default="INFO", choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"], help="log level")

    clargs = parser.parse_args()

    _logger.setLevel(clargs.log_level)

    post_retrieve(clargs.source, clargs.run_info)


def post_retrieve(source, fn_run_info):
    if not os.path.exists(fn_run_info):
        raise SystemExit(f"run_info file {fn_run_info} not found")

    run_info = json_load(fn_run_info)

    entry_name = ENTRY_NAMES[source]
    ftype      = FTYPES[source]
    writer     = WRITERS[source]

    if entry_name not in run_info:
        raise SystemExit(f'no "{entry_name}" defined in run_info file')

    channels = run_info[entry_name]

    data_request = {
        "range": {
            "startPulseId": run_info["start_pulseid"],
            "endPulseId":   run_info["stop_pulseid"]
        },
        "channels": [
            {
                "name": ch,
                "backend": config.IMAGE_BACKEND if ch.endswith(":FPICTURE") else config.DATA_BACKEND
            }
            for ch in channels
        ]
    }

    run_number         = run_info.get("run_number", 0)
    acquisition_number = run_info.get("acquisition_number", 0)

    ri_beamline = run_info["beamline"]
    ri_pgroup   = run_info["pgroup"]

    list_data_directories_run = glob(f"/sf/{ri_beamline}/data/{ri_pgroup}/raw/run{run_number:04}*")
    if len(list_data_directories_run) != 1:
        raise SystemExit(f"run directories ambiguous: {list_data_directories_run}")

    data_directory = list_data_directories_run[0]

    output_file = f"{data_directory}/data/acq{acquisition_number:04}.{ftype}.h5.2"

    parameters = None
    writer(data_request, output_file, parameters)

#    metadata = {
#        "general/user": run_info["pgroup"],
#        "general/process": __name__,
#        "general/created": str(datetime.now()),
#        "general/instrument": run_info["beamline"]
#    }





if __name__ == "__main__":
    run()


