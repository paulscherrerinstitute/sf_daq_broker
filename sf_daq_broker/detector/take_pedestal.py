import logging
from time import sleep

import epics
from slsdet import Jungfrau, gainMode


_logger = logging.getLogger("broker_writer")

PULSE_ID_SOURCE = "SLAAR11-LTIM01-EVR0:RX-PULSEID"



def take_pedestal(detectors_name, rate=1):
    if not detectors_name:
        return None, None

    detectors_number = [int(detector_name[2:4]) for detector_name in detectors_name]
    detectors = [Jungfrau(detector_number) for detector_number in detectors_number]

    pulse_id_pv = epics.PV(PULSE_ID_SOURCE)

    # switch to G0
    for detector in detectors:
        detector.gainmode = gainMode.DYNAMIC

    sleep(1)

    start_pulse_id = int(pulse_id_pv.get())

    # collect in G0
    sleep(10 * rate)

    # switch to G1
    for detector in detectors:
        detector.gainmode = gainMode.FORCE_SWITCH_G1

    # collect in G1
    sleep(10 * rate)

    # switch to G2
    for detector in detectors:
        detector.gainmode = gainMode.FORCE_SWITCH_G2

    # collect in G2
    sleep(10*rate)

    stop_pulse_id = int(pulse_id_pv.get())

    # switch back to dynamic mode
    for detector in detectors:
        detector.gainmode = gainMode.DYNAMIC

    sleep(1)

    det_start_pulse_id = 0
    det_stop_pulse_id = stop_pulse_id
    for p in range(start_pulse_id, stop_pulse_id+1):
        if p % rate == 0:
            det_stop_pulse_id = p
            if det_start_pulse_id == 0:
                det_start_pulse_id = p

    return det_start_pulse_id, det_stop_pulse_id



