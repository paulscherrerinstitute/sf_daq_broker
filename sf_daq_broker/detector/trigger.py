from time import sleep

import epics

from sf_daq_broker.errors import TriggerError, ValidationError
from sf_daq_broker.utils import typename


BEAMLINE_EVENT_CODE = {
    "alvra"       : "SAR-CVME-TIFALL4-EVG0:SoftEvt-EvtCode-SP",
    "bernina"     : "SAR-CVME-TIFALL5-EVG0:SoftEvt-EvtCode-SP",
    "cristallina" : "SAR-CVME-TIFALL6-EVG0:SoftEvt-EvtCode-SP",
    "diavolezza"  : "SAT-CVME-TIFALL4-EVG0:SoftEvt-EvtCode-SP",
    "maloja"      : "SAT-CVME-TIFALL5-EVG0:SoftEvt-EvtCode-SP",
    "furka"       : "SAT-CVME-TIFALL6-EVG0:SoftEvt-EvtCode-SP"
}

TRIGGER_VALUES = {
    "start": 254,
    "stop":  255
}

TRIGGER_VALUES_INVERTED = {v: k for k, v in TRIGGER_VALUES.items()}



class Trigger:

    def __init__(self, beamline):
        self.beamline = beamline
        validate_beamline(beamline)

        pvname = BEAMLINE_EVENT_CODE[beamline]

        try:
            self.pv = epics.PV(pvname)
        except Exception as e:
            raise TriggerError(f"could not connect to {beamline} event code PV {pvname}") from e


    def start(self):
        set_trigger(self.pv, "start")

    def stop(self):
        set_trigger(self.pv, "stop")

    def __repr__(self):
        tname = typename(self)
        status = self.pv.get()
        status = TRIGGER_VALUES_INVERTED.get(status, status)
        return f"{tname} {self.beamline}: {status}"



def validate_beamline(beamline):
    #TODO: is the None check even needed?
    if beamline is None:
        raise ValidationError("no beamline given")

    if beamline not in BEAMLINE_EVENT_CODE:
        raise ValidationError(f"trigger event code for beamline {beamline} not known")



def set_trigger(pv, action):
    value = TRIGGER_VALUES[action]

    try:
        pv.put(value)
    except Exception as e:
        raise TriggerError(f"could not {action} detector trigger {pv.pvname}") from e

    # sleep to give epics a chance to process change
    sleep(4) #TODO: this seems excessive, check!

    try:
        event_code = int(pv.get())
    except Exception as e:
        raise TriggerError(f"got unexpected value from detector trigger {pv.pvname}: {pv.get()}") from e

    if event_code != value:
        raise TriggerError(f"detector trigger {pv.pvname} did not {action} (expected {value} but event returned {event_code})")



