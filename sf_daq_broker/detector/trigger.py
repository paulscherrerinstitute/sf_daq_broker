from time import sleep

import epics

from sf_daq_broker.errors import TriggerError, ValidationError


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

        if beamline not in BEAMLINE_EVENT_PV:
            raise ValidationError(f"detector trigger event code PV for beamline {beamline} not known")

        pvname = BEAMLINE_EVENT_PV[beamline]

        self.name = f"{beamline} detector trigger ({pvname})"

        try:
            self.pv = epics.PV(pvname)
        except Exception as e:
            raise TriggerError(f"could not connect to {self.name}") from e


    def start(self):
        self.set("start")

    def stop(self):
        self.set("stop")


    def set(self, action):
        pv = self.pv
        value = EVENT_COMMANDS[action]

        errmsg = f"could not {action} {self.name}"

        try:
            pv.put(value)
        except Exception as e:
            raise TriggerError(f"{msg} (could not write to PV)") from e

        # sleep to give epics a chance to process change
        sleep(4) #TODO: this seems excessive, check!

        try:
            new_value = pv.get()
        except Exception as e:
            raise TriggerError(f"{msg} (could not read from PV)") from e

        try:
            new_value = int(new_value)
            if new_value != value:
                raise ValueError
        except Exception as e:
            raise TriggerError(f"{msg} (expected {value} but received {new_value})") from e


    @property
    def status(self):
        res = self.pv.get()
        res = EVENT_STATES.get(res, f"{res}?")
        return res

    def __repr__(self):
        return f"{self.name}: {self.status}"



