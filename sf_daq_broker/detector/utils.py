from .detector_config import _daq_beamline, _detector_daq, _detector_names


def detector_human_names():
    return _detector_names


def get_streamvis_address():
    address = {}
    for d in _detector_daq:
        detector_number = int(d[2:4])
        daq = _detector_daq[d]["daq"]
        address[d] = f"sf-daq-{daq}:{5000 + detector_number}"
    return address


def configured_detectors_for_beamline(beamline=None):
    detectors = []
    if beamline is None:
        return detectors

    for detector_name in _detector_daq:
        daq = _detector_daq[detector_name]["daq"]
        port = _detector_daq[detector_name]["port"]
        if daq in _daq_beamline and port in _daq_beamline[daq]:
            if _daq_beamline[daq][port] == beamline:
                detectors.append(detector_name)

    return detectors



