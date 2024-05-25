import logging

from slsdet import Jungfrau, gainMode, timingMode

from sf_daq_broker.detector.detector_config import DetectorConfig, DETECTOR_NAMES
from sf_daq_broker.detector.trigger import Trigger
from sf_daq_broker.errors import TriggerError, ValidationError


_logger = logging.getLogger("broker_writer")



def power_on_detector(detector_name, beamline):
    _logger.info(f"request to power on detector {detector_name}")

    try:
        validate_detector_name(detector_name)
    except ValidationError as e:
        _logger.error(e)
        return

    try:
        detector_config = DetectorConfig(detector_name)
    except Exception:
        _logger.exception(f"could not load config for detector {detector_name}")
        return

    detector_number = int(detector_name[2:4])

    try:
        detector = Jungfrau(detector_number)
    except Exception:
        _logger.exception(f"could not connect to detector {detector_name} (number {detector_number})")
        return

    try:
        trigger = Trigger(beamline)
        trigger.stop()
    except (TriggerError, ValidationError) as e:
        _logger.error(e, exc_info=e.__cause__)
        return

    try:
        detector.stopDetector()
    except Exception as e:
        _logger.info(f"could not stop detector {detector_name}", exc_info=e)

    try:
        detector.freeSharedMemory()
    except Exception:
        _logger.exception(f"could not free shared memory of detector {detector_name}")

    try:
        apply_detector_config(detector_config, detector)
    except Exception:
        _logger.exception(f"could not apply config to detector {detector_name}")

    try:
        detector.startDetector()
    except Exception:
        _logger.exception(f"could not start detector {detector_name}")

    try:
        trigger.start()
    except TriggerError as e:
        _logger.error(e, exc_info=e.__cause__)
        return

    _logger.info(f"detector {detector_name} powered on")


def validate_detector_name(detector_name):
    #TODO: is the None check even needed?
    if detector_name is None:
        raise ValidationError("no detector name given")

    if detector_name not in DETECTOR_NAMES:
        raise ValidationError(f"detector name {detector_name} not known")


def apply_detector_config(detector_configuration, detector):
    detector_number = detector_configuration.get_detector_number()
#    number_modules = detector_configuration.get_number_modules()

    detector.detsize = detector_configuration.get_detector_size()

    detector.setHostname(detector_configuration.get_detector_hostname())

    detector.udp_dstmac = detector_configuration.get_detector_udp_dstmac()
    detector.udp_dstip  = detector_configuration.get_udp_dstip()
    detector.udp_dstport = detector_configuration.get_detector_port_first_module() # increments port by +1 for each module

    detector.udp_srcip = detector_configuration.get_detector_upd_ip()
    detector.udp_srcmac = detector_configuration.get_detector_udp_mac()

    detector.txdelay_frame = detector_configuration.get_detector_txndelay()
    detector.delay = detector_configuration.get_detector_delay()

    if detector_number == 2:
        detector.dacs.vb_comp = 1420

    if detector_number == 18:
        detector.dacs.vb_comp = 1320

    # workaround for mismatched frames problem
    if detector_number == 6:
        detector.sync = 1
        detector.setMaster(1, 31)

    # hardcoded fixed gain for specific modules
    if detector_number == 6:
        modules = [
            3, 4,
            6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
            23, 24
        ]
        detector.setGainMode(gainMode.FORCE_SWITCH_G1, modules)

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



