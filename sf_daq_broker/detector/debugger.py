from collections import defaultdict

from sf_daq_broker.utils import typename

from .detector_config import DETECTOR_NAMES, DetectorConfig
from .detector import Detector
from .power_on_detector import power_on_detector
from .trigger import Trigger


class Debugger:
    """
    centralized detector/trigger interactions for debugging in ipython
    """

    def __init__(self, ID_or_name):
        self.ID, self.name = _ID, name = parse_ID_or_name(ID_or_name)
        self.config = config = DetectorConfig(name)
        self.beamline = beamline = config.get_beamline()
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



def parse_ID_or_name(ID_or_name):
    parse = parse_name if isinstance(ID_or_name, str) else parse_ID
    return parse(ID_or_name)

def parse_name(name):
    if name not in DETECTOR_NAMES:
        printable_detector_names = mk_printable(DETECTOR_NAMES)
        raise ValueError(f"detector name {name} unknown -- choose from: {printable_detector_names}")
    ID = name_to_ID(name)
    return ID, name

def parse_ID(ID):
    detector_ID_to_name = mk_mapping()
    names = detector_ID_to_name.get(ID)
    if not names:
        printable_ids = mk_printable(detector_ID_to_name)
        raise ValueError(f"ID {ID} unknown -- choose from: {printable_ids}")
    if len(names) != 1:
        printable_names = mk_printable(names)
        raise ValueError(f"ID {ID} ambiguous -- choose from: {printable_names}")
    name = names[0]
    return ID, name

def mk_mapping():
    detector_ID_to_name = defaultdict(list)
    for n in DETECTOR_NAMES:
        ID = name_to_ID(n)
        detector_ID_to_name[ID].append(n)
    detector_ID_to_name = dict(detector_ID_to_name)
    return detector_ID_to_name

def name_to_ID(n):
    return int(n[2:4])

def mk_printable(seq):
    return ", ".join(repr(i) for i in sorted(seq))


def str_or_exc(x):
    try:
        return str(x)
    except Exception as e:
        en = typename(e)
        return f"<{en}: {e}>"



