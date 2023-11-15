from slsdet import Jungfrau
from slsdet.enums import timingMode, detectorSettings

import epics

from time import sleep

import logging

from sf_daq_broker.detector.detector_config import DetectorConfig

_logger = logging.getLogger("broker_writer")

beamline_event_code = { "alvra"       : "SAR-CVME-TIFALL4-EVG0:SoftEvt-EvtCode-SP",
                        "bernina"     : "SAR-CVME-TIFALL5-EVG0:SoftEvt-EvtCode-SP", 
                        "cristallina" : "SAR-CVME-TIFALL6-EVG0:SoftEvt-EvtCode-SP",
                        "furka"       : "SAT-CVME-TIFALL6-EVG0:SoftEvt-EvtCode-SP",
                        "maloja"      : "SAT-CVME-TIFALL5-EVG0:SoftEvt-EvtCode-SP"
                      }


def load_detector_config(detector_name=None):

    _logger.info(f'request to load config for detector {detector_name}')

    if detector_name is None:
        _logger.error("No detector name given")
        return

    detector_configuration = DetectorConfig(detector_name)

    if not detector_configuration.is_configuration_present():
        _logger.error("No detector configuration present")
        return

    detector_number = detector_configuration.get_detector_number()
    number_modules = detector_configuration.get_number_modules()

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

    detector.temp_threshold = detector_configuration.get_detector_temp_threshold()
    detector.temp_control = 1

    detector.powerchip = True
    detector.highvoltage = 120

    detector.timing = timingMode.TRIGGER_EXPOSURE
    detector.triggers = 500000000
    if detector_number == 15:
        detector.exptime = 10e-06
    else:
        detector.exptime = 5e-06
    detector.frames = 1
    detector.dr = 16

    detector.startDetector()



def power_on_detector(detector_name=None, beamline=None):

    _logger.info(f'request to power on detector {detector_name}') 

    if detector_name is None:
        _logger.error("No detector name given")
        return

    if beamline is None:
        _logger.error("No beamline name is given")
        return

    if beamline not in beamline_event_code:
        _logger.error(f"Dont know how to stop event code for this beamline {beamline}")
        return

    event_code_pv_name = beamline_event_code[beamline]
    event_code_pv = epics.PV(event_code_pv_name)

    if detector_name[:2] != "JF":
        _logger.error(f'Not a Jungfrau detector name {detector_name}')
        return

    if len(detector_name) != 10:
        _logger.error(f'Not proper name of detector {detector_name}')
        return

    detector_number = int(detector_name[2:4])

    # stop triggering of the beamline detectors
    try:
        event_code_pv.put(255) 
    except Exception as e:
        _logger.error(f"can not stop detector triggering : {e}")
        return

    #sleep few second to give epics a chance to switch code
    sleep(4)

    event_code = int(event_code_pv.get())
    if event_code != 255:
        _logger.error(f"trigger is not stopped {event_code}")
        return

    detector = Jungfrau(detector_number)
    
    try:
        detector.stopDetector()
    except:
        _logger.info(f'{detector_name} (number {detector_number}) can not be stopped, may be was not initialised before')

    detector.freeSharedMemory()

    try:
        load_detector_config(detector_name)

    except Exception as e:
        _logger.error(f'cant configure detector : {e}')

    # start triggering
    event_code_pv.put(254)
