from time import sleep

import epics

from sf_daq_broker.errors import TriggerError, ValidationError
from sf_daq_broker.utils import typename


BEAMLINE_EVENT_PV = {
    "alvra"       : "SAR-CVME-TIFALL4-EVG0:SoftEvt-EvtCode-SP",
    "bernina"     : "SAR-CVME-TIFALL5-EVG0:SoftEvt-EvtCode-SP",
    "cristallina" : "SAR-CVME-TIFALL6-EVG0:SoftEvt-EvtCode-SP",
    "diavolezza"  : "SAT-CVME-TIFALL4-EVG0:SoftEvt-EvtCode-SP",
    "maloja"      : "SAT-CVME-TIFALL5-EVG0:SoftEvt-EvtCode-SP",
    "furka"       : "SAT-CVME-TIFALL6-EVG0:SoftEvt-EvtCode-SP"
}


# (value, command, state)
EVENT_MAP = (
    (254, "start", "running"),
    (255, "stop",  "stopped")
)

EVENT_COMMANDS = {cmd: val for val, cmd, _sta in EVENT_MAP} # for put
EVENT_STATES   = {val: sta for val, _cmd, sta in EVENT_MAP} # for get



class Trigger:

    def __init__(self, beamline):
        self.beamline = beamline
        validate_beamline(beamline)

        pvname = BEAMLINE_EVENT_PV[beamline]

        try:
            self.pv = epics.PV(pvname)
        except Exception as e:
            raise TriggerError(f"could not connect to {beamline} event code PV {pvname}") from e


    def start(self):
        self.set_trigger("start")

    def stop(self):
        self.set_trigger("stop")


    def set_trigger(self, action):
        pv = self.pv
        value = EVENT_COMMANDS[action]

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


    @property
    def status(self):
        res = self.pv.get()
        res = EVENT_STATES.get(res, f"{res}?")
        return res

    def __repr__(self):
        tname = typename(self)
        return f"{tname} {self.beamline}: {self.status}"



def validate_beamline(beamline):
    #TODO: is the None check even needed?
    if beamline is None:
        raise ValidationError("no beamline given")

    if beamline not in BEAMLINE_EVENT_PV:
        raise ValidationError(f"trigger event code for beamline {beamline} not known")



