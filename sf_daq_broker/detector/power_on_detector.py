import logging
from time import sleep

import epics
from slsdet import Jungfrau
from slsdet.enums import timingMode

from sf_daq_broker.detector.detector_config import DetectorConfig


_logger = logging.getLogger("broker_writer")


BEAMLINE_EVENT_CODE = {
    "alvra"       : "SAR-CVME-TIFALL4-EVG0:SoftEvt-EvtCode-SP",
    "bernina"     : "SAR-CVME-TIFALL5-EVG0:SoftEvt-EvtCode-SP",
    "cristallina" : "SAR-CVME-TIFALL6-EVG0:SoftEvt-EvtCode-SP",
    "diavolezza"  : "SAT-CVME-TIFALL4-EVG0:SoftEvt-EvtCode-SP",
    "maloja"      : "SAT-CVME-TIFALL5-EVG0:SoftEvt-EvtCode-SP",
    "furka"       : "SAT-CVME-TIFALL6-EVG0:SoftEvt-EvtCode-SP"
}



def power_on_detector(detector_name, beamline):
    _logger.info(f"request to power on detector {detector_name}")

    if detector_name is None:
        _logger.error("no detector name given")
        return

    if beamline is None:
        _logger.error("no beamline name given")
        return

    if beamline not in BEAMLINE_EVENT_CODE:
        _logger.error(f"trigger event code for beamline {beamline} not configured")
        return

    event_code_pv_name = BEAMLINE_EVENT_CODE[beamline]
    event_code_pv = epics.PV(event_code_pv_name)

    if detector_name[:2] != "JF":
        _logger.error(f'detector name {detector_name} does not start with "JF"')
        return

    if len(detector_name) != 10:
        _logger.error(f"detector name {detector_name} does not have 10 characters")
        return

    detector_number = int(detector_name[2:4])

    # stop trigger of the current beamline's detectors
    try:
        event_code_pv.put(255)
    except Exception as e:
        _logger.error(f"cannot stop detector trigger {event_code_pv_name} (due to: {e})")
        return

    # sleep to give epics a chance to process change
    sleep(4)

    event_code = int(event_code_pv.get())
    if event_code != 255:
        _logger.error(f"detector trigger {event_code_pv_name} did not stop (event returned {event_code})")
        return

    detector = Jungfrau(detector_number)

    try:
        detector.stopDetector()
    except Exception as e:
        _logger.info(f"detector {detector_name} (number {detector_number}) could not be stopped (due to: {e})")

    detector.freeSharedMemory()

    try:
        load_detector_config(detector_name)
    except Exception as e:
        _logger.error(f"could not configure detector {detector_name} (due to: {e})")

    # start trigger
    event_code_pv.put(254)


def load_detector_config(detector_name):
    _logger.info(f"request to load config for detector {detector_name}")

    try:
        detector_configuration = DetectorConfig(detector_name)
    except RuntimeError as e:
        _logger.error(f"cannot configure detector {detector_name} (due to: {e})")
        return

    detector_number = detector_configuration.get_detector_number()
#    number_modules = detector_configuration.get_number_modules()

    detector = Jungfrau(detector_number)

    detector.detsize = detector_configuration.get_detector_size()

    detector.setHostname(detector_configuration.get_detector_hostname())

    detector.udp_dstmac = detector_configuration.get_detector_udp_dstmac()
    detector.udp_dstip  = detector_configuration.get_udp_dstip()
    detector.udp_dstport = detector_configuration.get_detector_port_first_module() # will increment port(+1) for each module

    detector.udp_srcip = detector_configuration.get_detector_upd_ip()
    detector.udp_srcmac = detector_configuration.get_detector_udp_mac()

    detector.txndelay_frame = detector_configuration.get_detector_txndelay()
    detector.delay = detector_configuration.get_detector_delay()

    if detector_number == 2:
        detector.dacs.vb_comp = 1420

    if detector_number == 18:
        detector.dacs.vb_comp = 1320

    detector.temp_threshold = detector_configuration.get_detector_temp_threshold()
    detector.temp_control = 1

    detector.powerchip = True
    detector.highvoltage = 120
    if detector_number == 18:
        detector.highvoltage = 0

    detector.timing = timingMode.TRIGGER_EXPOSURE
    detector.triggers = 500000000

    detector.exptime = 5e-06
    if detector_number == 15:
        detector.exptime = 10e-06

    detector.frames = 1
    detector.dr = 16

    detector.startDetector()



