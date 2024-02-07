from .detector_config import DAQ_BEAMLINE, DETECTOR_DAQ, DETECTOR_NAMES


def detector_human_names():
    return DETECTOR_NAMES


def get_streamvis_address():
    address = {}
    for d in DETECTOR_DAQ:
        detector_number = int(d[2:4])
        daq = DETECTOR_DAQ[d]["daq"]
        address[d] = f"sf-daq-{daq}:{5000 + detector_number}"
    return address


def get_configured_detectors(beamline):
    detectors = []
    for detector_name in DETECTOR_DAQ:
        daq  = DETECTOR_DAQ[detector_name]["daq"]
        port = DETECTOR_DAQ[detector_name]["port"]
        if daq in DAQ_BEAMLINE and port in DAQ_BEAMLINE[daq]:
            if DAQ_BEAMLINE[daq][port] == beamline:
                detectors.append(detector_name)

    if not detectors:
        raise RuntimeError(f"no detectors configured for beamline {beamline}")

    return detectors



