from slsdet import Jungfrau, detectorSettings
from time import sleep

import epics

import logging

_logger = logging.getLogger("broker_writer")

pulse_id_source = "SLAAR11-LTIM01-EVR0:RX-PULSEID"

def take_pedestal(detectors_name=[], rate=1):

    if len(detectors_name) < 1:
        return None, None

    detectors_number = [int(detector_name[2:4]) for detector_name in detectors_name]

    detectors = [Jungfrau(detector_number) for detector_number in detectors_number]

    pulse_id_pv = epics.PV(pulse_id_source)

    # reset bits
    for detector in detectors:
        detector.settings = detectorSettings.DYNAMICGAIN
    sleep(1)

    start_pulse_id = int(pulse_id_pv.get())

    #G0
    for detector in detectors:
        detector.settings = detectorSettings.DYNAMICGAIN
    sleep(10*rate)

    #G1
    for detector in detectors:
        detector.settings = detectorSettings.FORCESWITCHG1
    sleep(10*rate)

    #G2
    for detector in detectors:
        detector.settings = detectorSettings.FORCESWITCHG2
    sleep(10*rate)

    stop_pulse_id = int(pulse_id_pv.get())

    # reset bits
    for detector in detectors:
        detector.settings = detectorSettings.DYNAMICGAIN
    sleep(1)

    det_start_pulse_id = 0
    det_stop_pulse_id = stop_pulse_id
    for p in range(start_pulse_id, stop_pulse_id+1):
        if p%rate == 0:
            det_stop_pulse_id = p
            if det_start_pulse_id == 0:
                det_start_pulse_id = p

    return det_start_pulse_id, det_stop_pulse_id
