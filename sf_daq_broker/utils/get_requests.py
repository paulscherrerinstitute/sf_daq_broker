from time import time

from sf_daq_broker import config


def get_data_api_request(channels, start_pulse_id, stop_pulse_id):
    channels = [
        {
            "name": ch,
            "backend": config.IMAGE_BACKEND if ch.endswith(":FPICTURE") else config.DATA_BACKEND
        }
        for ch in channels
    ]
    res = {
        "channels": channels,
        "range": {
            "startPulseId": start_pulse_id,
            "endPulseId": stop_pulse_id
        },
        "response": {
            "format": "json",
            "compression": "none"
        },
        "eventFields": ["channel", "pulseId", "value", "shape", "globalDate"],
        "configFields": ["type", "shape"]
    }
    return res


def get_writer_request(writer_type, channels, output_file, metadata, start_pulse_id, stop_pulse_id, run_log_file):
    res = {
        "writer_type": writer_type,
        "channels": channels,

        "start_pulse_id": start_pulse_id,
        "stop_pulse_id": stop_pulse_id,

        "output_file": output_file,
        "run_log_file": run_log_file,

        "metadata": metadata,
        "timestamp": time()
    }
    return res



