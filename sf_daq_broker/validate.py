import os
from glob import glob

from sf_daq_broker.utils import dueto


MAX_PULSEID_DELTA = 60001
ALLOWED_RATE_MULTIPLICATORS = [1, 2, 4, 8, 10, 20, 40, 50, 100]


##TODO: use message templates?
#TEMPL_MISSING_PARAM = "no {what} provided in the request parameters"


## just check truthiness

def detectors(ds):
    if not ds:
        raise RuntimeError('no "detectors" provided in the request parameters')



##TODO: use generic truthiness check?

#def true(what, message):
#    if not what:
#        raise RuntimeError(message)

#def request(req):
#    true(req, "request parameters are empty")



# check more complex things

def request_has(req, *args):
    if not req:
        raise RuntimeError("no request parameters provided")

    for i in args:
        if i not in req:
            raise RuntimeError(f'no "{i}" provided in the request parameters')


def request_is_empty(req):
    if req:
        raise RuntimeError(f"this endpoint does not accept request parameters but received {req}")

def path_to_pgroup_exists(ptp):
    if not os.path.exists(ptp):
        raise RuntimeError(f"pgroup directory {ptp} not reachable")

def pgroup_is_not_closed_yet(dd, ptp):
    if os.path.exists(f"{dd}/CLOSED"):
        raise RuntimeError(f"pgroup directory {ptp} is already closed for writing")

def epics_config_file_exists(cf, bl):
    if not os.path.exists(cf):
        raise RuntimeError(f"epics buffer config file {cf} does not exist for beamline {bl}")

def pgroup_is_not_closed(dd, ptp):
    if os.path.exists(f"{dd}/CLOSED"):
        raise RuntimeError(f"pgroup directory {ptp} is closed for writing")

def detector_name_in_allowed_detectors_beamline(dn, adb, bl):
    if dn not in adb:
        raise RuntimeError(f"detector {dn} does not belong to beamline {bl}")

def all_detector_names_in_allowed_detectors_beamline(dns, adb, bl):
    for dn in dns:
        detector_name_in_allowed_detectors_beamline(dn, adb, bl)

def allowed_pulseid_range(pid_start, pid_stop):
    delta = pid_stop - pid_start
    if delta > MAX_PULSEID_DELTA:
        raise RuntimeError(f"requested number of pulses {delta} too large (max. {MAX_PULSEID_DELTA})")
    if delta < 0:
        raise RuntimeError(f"requested number of pulses {delta} negative")

def rate_multiplicator(rm):
    if rm not in ALLOWED_RATE_MULTIPLICATORS:
        raise RuntimeError('"rate_multiplicator" not from allowed values {ALLOWED_RATE_MULTIPLICATORS}')

def allowed_run_number(rn, ckrn):
    if rn > ckrn:
        raise RuntimeError(f'requested "run_number" {rn:04} not generated by sf-daq')

def tag_matching_previous(ptp, rn, rd, ut):
    runs = glob(f"{ptp}/run{rn:04}*")
    if runs and f"{ptp}{rd}" not in runs:
        raise RuntimeError(f"run {rn:04} exists already but with different tag(s) {runs} than the requested {ut}")

def request_detectors_is_dict(rd):
    if not isinstance(rd, dict):
        raise RuntimeError(f'"detectors" provided in the request parameters ({rd}) is not a dictionary')

def dap_parameters_file_exists(dpf):
    if not os.path.exists(dpf):
        raise RuntimeError(f"DAP parameter file {dpf} does not exist")

def run_dir_exists(lddr, rn):
    if not lddr:
        raise RuntimeError(f"run {rn:04} does not exist in this pgroup")



# checks with side effects -- move somewhere else? refactor logic?

def directory_exists(pd):
    if os.path.exists(pd):
        return
    try:
        os.makedirs(pd)
    except Exception as e:
        raise RuntimeError(f"cannot create directory {pd} {dueto(e)}") from e

def request_has_integer_pulseids(req):
    helper_request_has_integer_pulseid(req, "start_pulseid")
    helper_request_has_integer_pulseid(req, "stop_pulseid")

def helper_request_has_integer_pulseid(req, key):
    try:
        req[key] = int(req[key])
    except Exception as e:
        raise RuntimeError(f'bad "{key}" provided in the request parameters {dueto(e)}') from e



