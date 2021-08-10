import os
from slsdet import Jungfrau
from slsdet.enums import timingMode

import epics

from time import sleep

import logging

_logger = logging.getLogger("broker_writer")

beamline_event_code = { "alvra" :   "SAR-CVME-TIFALL4-EVG0:SoftEvt-EvtCode-SP",
                        "bernina" : "SAR-CVME-TIFALL5-EVG0:SoftEvt-EvtCode-SP", 
                        "maloja" :  "SAT-CVME-TIFALL5-EVG0:SoftEvt-EvtCode-SP"
                      }


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

    config_file = f'/home/dbe/git/sf_daq_broker/detector/{detector_name}.config'

    if not os.path.exists(config_file):
        _logger.error(f'{config_file} for {detector_name} does not exists')
        return

    # stop triggering of the beamline detectors
    try:
        event_code_pv.put(255) 
    except Exception as e:
        _logger.error(f"can not stop detector triggering : {e}")
        return

    event_code = int(event_code_pv.get())
    #sleep 1 second to give epics a chance to switch code
    sleep(1)
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
        detector.loadConfig(config_file)
        detector.powerchip = True
        detector.highvoltage = 120

        detector.stopDetector()
      
        detector.timing = timingMode.TRIGGER_EXPOSURE
        detector.triggers = 500000000
        if detector_number == 15:
            detector.exptime = 10e-06
        else:
            detector.exptime = 5e-06
        detector.frames = 1
        detector.dr = 16
        detector.clearBit(0x5d,0)

        detector.startDetector()

    except Exception as e:
        _logger.error(f'cant configure detector : {e}')

    # start triggering
    event_code_pv.put(254)
