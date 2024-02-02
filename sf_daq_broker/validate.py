import os
from glob import glob


# just check truthiness

def request(req):
    if not req:
        raise RuntimeError("request parameters are empty")

def remote_ip(ri):
    if not ri:
        raise RuntimeError("can not identify from which machine request were made")

def beamline(bl):
    if not bl:
        raise RuntimeError("can not determine from which console request came, rejected")

def allowed_detectors_beamline(adb):
    if not adb:
        raise RuntimeError("request is made from beamline which doesnt have detectors")

def detector_name(dn):
    if not dn:
        raise RuntimeError("no detector name in the request")

def detectors(ds):
    if not ds:
        raise RuntimeError("no detectors defined")



##TODO: use generic truthiness check?

#def true(what, message):
#    if not what:
#        raise RuntimeError(message)

#def request(req):
#    true(req, "request parameters are empty")



# check more complex things

def request_has_pgroup(req):
    if "pgroup" not in req:
        raise RuntimeError("no pgroup in request parameters")

def path_to_pgroup_exists(ptp):
    if not os.path.exists(ptp):
        raise RuntimeError(f"pgroup directory {ptp} not reachable")

def pgroup_is_not_closed_yet(dd, ptp):
    if os.path.exists(f"{dd}/CLOSED"):
        raise RuntimeError(f"{ptp} is already closed for writing")

def epics_config_file_exists(cf, bl):
    if not os.path.exists(cf):
        raise RuntimeError(f"epics config file not exist for this beamline {bl}")

def pgroup_is_not_closed(dd, ptp):
    if os.path.exists(f"{dd}/CLOSED"):
        raise RuntimeError(f"{ptp} is closed for writing")

def detector_name_in_allowed_detectors_beamline(dn, adb, bl):
    if dn not in adb:
        raise RuntimeError(f"{dn} not belongs to the {bl}")

def all_detector_names_in_allowed_detectors_beamline(dns, adb, bl):
    for dn in dns:
        detector_name_in_allowed_detectors_beamline(dn, adb, bl)

def request_has_detectors(req):
    if "detectors" not in req:
        raise RuntimeError("no detectors defined")

def request_has_pulseids(req):
    if "start_pulseid" not in req or "stop_pulseid" not in req:
        raise RuntimeError("no start or stop pluseid provided in request parameters")

def allowed_pulseid_range(pid_start, pid_stop):
    delta = pid_stop - pid_start
    if delta > 60001 or delta < 0:
        raise RuntimeError("number of pulse_id problem: too large or negative request")

def rate_multiplicator(rm):
    if rm not in [1, 2, 4, 8, 10, 20, 40, 50, 100]:
        raise RuntimeError("rate_multiplicator is not allowed one")

def allowed_run_number(rn, ckrn):
    if rn > ckrn:
        raise RuntimeError(f"requested run_number {rn} generated not by sf-daq")

def tag_matching_previous(ptp, rn, rd, ut):
    list_data_directories_run = glob(f"{ptp}/run{rn:04}*")
    if list_data_directories_run:
        if f"{ptp}{rd}" not in list_data_directories_run:
            raise RuntimeError(f"data directory for this run {rn:04} already exists with different tag: {list_data_directories_run}, than requested {ut}")

def request_detectors_is_dict(rd):
    if not isinstance(rd, dict):
        raise RuntimeError(f"{rd} is not dictionary")

def dap_parameters_file_exists(dpf):
    if not os.path.exists(dpf):
        raise RuntimeError("dap parameters file is not existing, contact support")

def request_has_run_number(rn):
    if rn is None:
        raise RuntimeError("no run_number in request parameters")

def run_dir_exists(lddr, rn):
    if not lddr:
        raise RuntimeError(f"no such run {rn} in the pgroup")



# checks with side effects -- move somewhere else? refactor logic?

def directory_exists(pd):
    if not os.path.exists(pd):
        try:
            os.makedirs(pd)
        except Exception as e:
            raise RuntimeError(f"no permission or possibility to make directory in pgroup space {pd} (due to: {e})") from e

def request_has_integer_pulseids(req):
    try:
        req["start_pulseid"] = int(req["start_pulseid"])
        req["stop_pulseid"]  = int(req["stop_pulseid"])
    except Exception as e:
        raise RuntimeError(f"bad start or stop pluseid provided in request parameters (due to: {e})") from e



