from time import sleep

import epics
from slsdet import Jungfrau, gainMode, pedestalParameters


PULSE_ID_SOURCE = "SLAAR11-LTIM01-EVR0:RX-PULSEID"



def take_pedestal(detectors_name, rate=1):
    if not detectors_name:
        return None, None

    detectors_number = [int(detector_name[2:4]) for detector_name in detectors_name]
    detectors = [Jungfrau(detector_number) for detector_number in detectors_number]

    #TODO: add a proper switch for this
    if detectors == ["JF01T03V01"]:
        switch_gains = switch_gains_via_pedestalmode
    else:
        switch_gains = switch_gains_manually

    start_pulse_id, stop_pulse_id = switch_gains(detectors, rate)
    det_start_pulse_id, det_stop_pulse_id = align_pids(start_pulse_id, stop_pulse_id, rate)
    return det_start_pulse_id, det_stop_pulse_id


def switch_gains_manually(detectors, rate):
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
    sleep(10 * rate)

    stop_pulse_id = int(pulse_id_pv.get())

    # switch back to dynamic mode
    for detector in detectors:
        detector.gainmode = gainMode.DYNAMIC

    sleep(1)

    return start_pulse_id, stop_pulse_id


def switch_gains_via_pedestalmode(detectors, rate):
    pulse_id_pv = epics.PV(PULSE_ID_SOURCE)

    pp = pedestalParameters()
    pp.frames = 50
    pp.loops = 200

    start_pulse_id = int(pulse_id_pv.get())

    # turn on pedestal mode
    for detector in detectors:
        detector.pedestalmode = pp

    ngains = 2 # g1 and g2
    sleep(ngains * pp.frames * pp.loops * rate)

    stop_pulse_id = int(pulse_id_pv.get())

    # turn off pedestal mode
    for detector in detectors:
        detector.pedestalmode = 0

    sleep(1)

    return start_pulse_id, stop_pulse_id


def align_pids(start_pulse_id, stop_pulse_id, rate):
    det_start_pulse_id = 0
    det_stop_pulse_id = stop_pulse_id
    for p in range(start_pulse_id, stop_pulse_id+1):
        if p % rate == 0:
            det_stop_pulse_id = p
            if det_start_pulse_id == 0:
                det_start_pulse_id = p

    return det_start_pulse_id, det_stop_pulse_id



