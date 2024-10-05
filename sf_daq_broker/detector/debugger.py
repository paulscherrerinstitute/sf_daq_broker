from sf_daq_broker.utils import typename

from .detector_config import DETECTOR_NAMES, DetectorConfig
from .detector import Detector
from .power_on_detector import power_on_detector
from .trigger import Trigger


DETECTOR_ID_TO_NAME = {int(n[2:4]): n for n in DETECTOR_NAMES}


class Debugger:
    """
    centralized detector/trigger interactions for debugging in ipython
    """

    def __init__(self, ID):
        self.ID = ID
        self.name = name = DETECTOR_ID_TO_NAME[ID]
        self.config = config = DetectorConfig(name)
        self.beamline = beamline = config.get_detector_beamline()
        self.detector = Detector(name)
        self.trigger = Trigger(beamline)

    def __repr__(self):
        attrs = (
            "name",
            "ID",
            "beamline",
            "detector",
            "trigger"
        )
        values = {name: str_or_exc(getattr(self, name)) for name in attrs}
        return "\n".join(f"{k}: {v}" for k, v in values.items())

    def start(self):
        self.detector.start()
        self.trigger.start()

    def stop(self):
        self.trigger.stop()
        self.detector.stop()

    def power_on(self):
        power_on_detector(self.name, self.beamline)



def str_or_exc(x):
    try:
        return str(x)
    except Exception as e:
        en = typename(e)
        return f"<{en}: {e}>"



