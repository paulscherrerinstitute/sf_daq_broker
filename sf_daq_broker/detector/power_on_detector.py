import logging

from sf_daq_broker.detector.detector import Detector
from sf_daq_broker.detector.trigger import Trigger
from sf_daq_broker.errors import DetectorError, TriggerError, ValidationError


_logger = logging.getLogger("broker_writer")



def power_on_detector(detector_name, beamline):
    _logger.info(f"request to power on detector {detector_name}")

    try:
        detector = Detector(detector_name)
        trigger = Trigger(beamline)
        trigger.stop()
    except (DetectorError, TriggerError, ValidationError) as e:
        _logger.error(e, exc_info=e.__cause__)
        raise e

    # stop is allowed to fail if this is not a restart
    try:
        detector.stop()
    except DetectorError as e:
        _logger.info(e, exc_info=e.__cause__)

    try:
        detector.free_shared_memory()
        detector.connect()
        detector.apply_config()
        detector.start()
    except DetectorError as e:
        _logger.error(e, exc_info=e.__cause__)
        raise e
    finally:
        try:
            trigger.start()
        except TriggerError as e:
            _logger.error(e, exc_info=e.__cause__)
            raise e

    _logger.info(f"detector {detector_name} powered on")



