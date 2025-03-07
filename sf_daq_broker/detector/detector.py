from collections import defaultdict

from .slsdetcompat import Jungfrau, detectorSettings, gainMode, pedestalParameters, timingMode

from sf_daq_broker.detector.detector_config import DETECTOR_NAMES, DetectorConfig
from sf_daq_broker.errors import DetectorError, ValidationError


def invert_dict(d):
    return dict(zip(d.values(), d.keys()))


DETECTOR_MODES = {
    "normal":    detectorSettings.GAIN0,
    "low_noise": detectorSettings.HIGHGAIN0
}

GAIN_MODES = {
    "dynamic":     gainMode.DYNAMIC,
    "fixed_gain1": gainMode.FORCE_SWITCH_G1,
    "fixed_gain2": gainMode.FORCE_SWITCH_G2
#    gainMode.FIX_G1
#    gainMode.FIX_G2
#    gainMode.FIX_G0
}

DETECTOR_MODE_NAMES = invert_dict(DETECTOR_MODES)
GAIN_MODE_NAMES     = invert_dict(GAIN_MODES)



class Detector:

    def __init__(self, name):
        validate_detector_name(name)
        self.name = name
        self.ID = int(name[2:4])
        self.load_config()
        self.connect()

    def start(self):
        try:
            self.jf.startDetector()
        except Exception as e:
            raise DetectorError(f"could not start detector {self.name}") from e

    def stop(self):
        try:
            self.jf.stopDetector()
        except Exception as e:
            raise DetectorError(f"could not stop detector {self.name}") from e

    @property
    def status(self):
        return self.jf.status

    def __repr__(self):
        status = self.status
        if isinstance(status, list):
            status = "\n" + "\n".join(f"{i}\t{s}" for i, s in enumerate(status))
        return f"{self.name}: {status}"

    def connect(self):
        try:
            self.jf = Jungfrau(self.ID)
        except Exception as e:
            raise DetectorError(f"could not connect to detector {self.name} (ID {self.ID})") from e

    def free_shared_memory(self):
        try:
            self.jf.freeSharedMemory()
        except Exception as e:
            raise DetectorError(f"could not free shared memory of detector {self.name}") from e

    def load_config(self):
        try:
            self.cfg = DetectorConfig(self.name)
        except Exception as e:
            raise DetectorError(f"could not load config for detector {self.name}") from e

    def apply_config(self):
        try:
            apply_detector_config(self.cfg, self.jf)
        except Exception as e:
            raise DetectorError(f"could not apply config to detector {self.name}") from e


    def get_temperatures(self):
        jf = self.jf
        temperatures = {t.name: jf.getTemperature(t) for t in jf.getTemperatureList()}
        temperatures["TEMPERATURE_THRESHOLDS"] = jf.getThresholdTemperature()
        return temperatures


    @property
    def exptime(self):
        return self.jf.exptime

    @exptime.setter
    def exptime(self, value):
        self.jf.exptime = value


    @property
    def delay(self):
        return self.jf.delay

    @delay.setter
    def delay(self, value):
        self.jf.delay = value


    @property
    def detector_mode(self):
        return DETECTOR_MODE_NAMES.get(self.jf.settings, "unknown")

    @detector_mode.setter
    def detector_mode(self, value):
        self.jf.settings = DETECTOR_MODES.get(value, "unknown")


    @property
    def gain_mode(self):
        gainmode = self.jf.gainmode
        if isinstance(gainmode, list):
            res = parse_param_list(gainmode)
            res = {GAIN_MODE_NAMES.get(k, "unknown"): v for k, v in res.items()}
            return res
        else:
            return GAIN_MODE_NAMES.get(gainmode, "unknown")

    @gain_mode.setter
    def gain_mode(self, value):
        if isinstance(value, dict):
            for k, v in value.items():
                k = GAIN_MODES.get(k, "unknown")
                self.jf.setGainMode(k, v)
        else:
            self.jf.gainmode = GAIN_MODES.get(value, "unknown")


    def enable_pedestal_mode(self, frames, loops):
        pp = pedestalParameters()
        pp.enable = 1
        pp.frames = frames
        pp.loops = loops
        self.jf.pedestalmode = pp

    def disable_pedestal_mode(self):
        pp = pedestalParameters()
        pp.enable = 0
        pp.frames = 0
        pp.loops = 0
        self.jf.pedestalmode = pp


    def power_on_modules(self, modules):
        self.jf.setPowerChip(True, modules)
        self.jf.setHighVoltage(120, modules)

    def power_off_modules(self, modules):
        self.jf.setHighVoltage(0, modules)
        self.jf.setPowerChip(False, modules)



def parse_param_list(seq):
    """
    convert list containg parameter value for each module into
    dict mapping parameter value to list of modules where it applies:
    [x, x, y, x] -> {x: [0, 1, 3], y: [2]}
    """
    res = defaultdict(list)
    for i, v in enumerate(seq):
        res[v].append(i)
    return res



def validate_detector_name(detector_name):
    #TODO: is the None check even needed?
    if detector_name is None:
        raise ValidationError("no detector name given")

    if detector_name not in DETECTOR_NAMES:
        raise ValidationError(f"detector name {detector_name} not known")



def apply_detector_config(detector_configuration, detector):
    detector_number = detector_configuration.get_number()
#    number_modules = detector_configuration.get_number_modules()

    detector.detsize = detector_configuration.get_size()

    detector.setHostname(detector_configuration.get_hostname())

    detector.udp_dstmac = detector_configuration.get_udp_dstmac()
    detector.udp_dstip  = detector_configuration.get_udp_dstip()
    detector.udp_dstport = detector_configuration.get_port_first_module() # increments port by +1 for each module

    detector.udp_srcip = detector_configuration.get_udp_ip()
    detector.udp_srcmac = detector_configuration.get_udp_mac()

    detector.txdelay_frame = detector_configuration.get_txndelay()
    detector.delay = detector_configuration.get_delay()

    if detector_number == 2:
        detector.dacs.vb_comp = 1420

    if detector_number == 18:
        detector.dacs.vb_comp = 1320

    if detector_number == 19:
        detector.dacs.vb_comp = 1050
        detector.dacs.vb_ds = 2400
        detector.dacs.vb_pixbuff = 550

    # workaround for mismatched frames problem
    if detector_number == 6:
        detector.sync = 1
        detector.setMaster(1, 0)

#    # hardcoded fixed gain for specific modules
#    if detector_number == 6:
#        modules = [
#            3, 4,
#            6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
#            23, 24
#        ]
#        detector.setGainMode(gainMode.FORCE_SWITCH_G1, modules)

    detector.temp_threshold = detector_configuration.get_temp_threshold()
    detector.temp_control = 1

    detector.powerchip = True
    detector.highvoltage = 120
    if detector_number == 18:
        detector.highvoltage = 0

    detector.timing = timingMode.TRIGGER_EXPOSURE
    detector.triggers = 500000000

    detector.exptime = 5e-06
    if detector_number == 15:
        detector.exptime = 10e-06

    detector.frames = 1
    detector.dr = 16



