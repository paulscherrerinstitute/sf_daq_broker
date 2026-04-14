
BEAMLINE_TO_PULSE_ID_PVS = {
    "alvra"  :     "SLAAR11-LTIM01-EVR0:RX-PULSEID",
    "bernina":     "SLAAR21-LTIM01-EVR0:RX-PULSEID",
    "cristallina": "SARES30-LTIM01-EVR0:RX-PULSEID",
    "diavolezza":  "SATES30-CVME-EVR0:RX-PULSEID", # fallback to furka
    "maloja" :     "SATES20-CVME-EVR0:RX-PULSEID",
    "furka":       "SATES30-CVME-EVR0:RX-PULSEID"
}


def get_pulse_id_pvname(beamline):
    try:
        return BEAMLINE_TO_PULSE_ID_PVS[beamline]
    except KeyError as e:
        raise ValueError(f"cannot match beamline {beamline} to PulseID PV") from e



