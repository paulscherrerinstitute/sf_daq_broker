import logging
from time import sleep

import epics

from sf_daq_broker.detector.detector import Detector


_logger = logging.getLogger("broker_writer")


PULSE_ID_SOURCE = "SLAAR11-LTIM01-EVR0:RX-PULSEID"



def take_pedestal(detector_names, rate=1, pedestalmode=False):
    if not detector_names:
        raise ValueError("no detector names provided")

    detectors = [Detector(name) for name in detector_names]

    if pedestalmode:
        mode = "via pedestalmode"
        switch_gains = switch_gains_via_pedestalmode
    else:
        mode = "manually"
        switch_gains = switch_gains_manually

    _logger.info(f"take_pedestal: switch gains {mode} for {detector_names}")

    start_pulse_id, stop_pulse_id = switch_gains(detectors, rate)
    det_start_pulse_id, det_stop_pulse_id = align_pids(start_pulse_id, stop_pulse_id, rate)
    return det_start_pulse_id, det_stop_pulse_id


def switch_gains_manually(detectors, rate):
    pulse_id_pv = epics.PV(PULSE_ID_SOURCE)

    # store original gain mode settings
    gain_mode_orig = {d.ID: d.gain_mode for d in detectors}

    # switch to G0
    for detector in detectors:
        detector.gain_mode = "dynamic"

    sleep(1)

    start_pulse_id = int(pulse_id_pv.get())

    # collect in G0
    sleep(10 * rate)

    # switch to G1
    for detector in detectors:
        detector.gain_mode = "fixed_gain1"

    # collect in G1
    sleep(10 * rate)

    # switch to G2
    for detector in detectors:
        detector.gain_mode = "fixed_gain2"

    # collect in G2
    sleep(10 * rate)

    stop_pulse_id = int(pulse_id_pv.get())

    # switch back to original gain mode settings
    for detector in detectors:
        detector.gain_mode = gain_mode_orig[detector.ID]

    sleep(1)

    return start_pulse_id, stop_pulse_id


def switch_gains_via_pedestalmode(detectors, rate):
    pulse_id_pv = epics.PV(PULSE_ID_SOURCE)

    # config
    frames = 50
    loops = 200

    # put detectors in idle mode
    for detector in detectors:
        detector.stop()

    # turn on pedestal mode
    for detector in detectors:
        detector.enable_pedestal_mode(frames, loops)

    start_pulse_id = int(pulse_id_pv.get())

    # start detectors again
    for detector in detectors:
        detector.start()

    ngains = 2 # g1 and g2
    nominal_rate = 100 # Hz
    wait_time = ngains * frames * loops * rate / nominal_rate
    sleep(wait_time)

    stop_pulse_id = int(pulse_id_pv.get())

    # put detectors in idle mode
    for detector in detectors:
        detector.stop()

    # turn off pedestal mode
    for detector in detectors:
        detector.disable_pedestal_mode()

    # start detectors again
    for detector in detectors:
        detector.start()

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



