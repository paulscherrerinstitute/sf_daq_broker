import logging

from sf_daq_broker.detector.detector_config import DetectorConfig
from sf_daq_broker.detector.detector import Detector
from sf_daq_broker.detector.trigger import Trigger
from sf_daq_broker.errors import DetectorError, TriggerError, ValidationError


_logger = logging.getLogger("broker_writer")



def power_on_detector(detector_name, beamline):
    _logger.info(f"request to power on detector {detector_name}")

    try:
        #TODO: detector_name is not validated
        detector_config = DetectorConfig(detector_name)
    except Exception:
        _logger.exception(f"could not load config for detector {detector_name}")
        return

    try:
        detector = Detector(detector_name)
    except (DetectorError, ValidationError) as e:
        _logger.error(e, exc_info=e.__cause__)
        return

    try:
        trigger = Trigger(beamline)
        trigger.stop()
    except (TriggerError, ValidationError) as e:
        _logger.error(e, exc_info=e.__cause__)
        return

    try:
        detector.stop()
    except DetectorError as e:
        _logger.info(e, exc_info=e.__cause__)

    try:
        detector.free_shared_memory()
        detector.apply_config(detector_config)
        detector.start()
    except DetectorError as e:
        _logger.error(e, exc_info=e.__cause__)

    try:
        trigger.start()
    except TriggerError as e:
        _logger.error(e, exc_info=e.__cause__)
        return

    _logger.info(f"detector {detector_name} powered on")



