import re
from collections import namedtuple


Jungfrau = namedtuple("Jungfrau", ("N", "T", "V"))

PATTERN_DET_NAME = re.compile(r"^JF(\d{2})T(\d{2})V(\d{2})$")
PATTERN_DET_NUM  = re.compile(r"^JF(\d{2})$")

def parse_det_name(det):
    match = PATTERN_DET_NAME.match(det)
    if not match:
        raise ValueError(f"{det} does not fit the pattern JFxxTyyVzz")
    return Jungfrau(*map(int, match.groups()))

def extract_det_num(det):
    match = PATTERN_DET_NUM.match(det)
    if not match:
        raise ValueError(f"{det} does not fit the pattern JFxx")
    return int(match.group(1))



