from slsdet import Jungfrau, detectorSettings, gainMode, timingMode

from sf_daq_broker.detector.detector_config import DETECTOR_NAMES, DetectorConfig
from sf_daq_broker.errors import DetectorError, ValidationError


def invert_dict(d):
    return dict(zip(d.values(), d.keys()))


DETECTOR_MODE_NAMES = {
    detectorSettings.GAIN0: "normal",
    detectorSettings.HIGHGAIN0: "low_noise"
}

GAIN_MODE_NAMES = {
    gainMode.DYNAMIC: "dynamic",
    gainMode.FORCE_SWITCH_G1: "fixed_gain1",
    gainMode.FORCE_SWITCH_G2: "fixed_gain2"
#    gainMode.FIX_G1
#    gainMode.FIX_G2
#    gainMode.FIX_G0
}

DETECTOR_MODES = invert_dict(DETECTOR_MODE_NAMES)
GAIN_MODES     = invert_dict(GAIN_MODE_NAMES)



class Detector:

    def __init__(self, name):
        validate_detector_name(name)
        self.name = name
        self.number = number = int(name[2:4])

        try:
            self.cfg = DetectorConfig(name)
        except Exception as e:
            raise DetectorError(f"could not load config for detector {name}") from e

        try:
            self.jf = Jungfrau(number)
        except Exception as e:
            raise DetectorError(f"could not connect to detector {name} (number {number})") from e


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

    def free_shared_memory(self):
        try:
            self.jf.freeSharedMemory()
        except Exception as e:
            raise DetectorError(f"could not free shared memory of detector {self.name}") from e

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
        self.jf.settings = DETECTOR_MODES.get(value)


    @property
    def gain_mode(self):
        return GAIN_MODE_NAMES.get(self.jf.gainmode, "unknown")

    @gain_mode.setter
    def gain_mode(self, value):
        self.jf.gainmode = GAIN_MODES.get(value)



def validate_detector_name(detector_name):
    #TODO: is the None check even needed?
    if detector_name is None:
        raise ValidationError("no detector name given")

    if detector_name not in DETECTOR_NAMES:
        raise ValidationError(f"detector name {detector_name} not known")



def apply_detector_config(detector_configuration, detector):
    detector_number = detector_configuration.get_detector_number()
#    number_modules = detector_configuration.get_number_modules()

    detector.detsize = detector_configuration.get_detector_size()

    detector.setHostname(detector_configuration.get_detector_hostname())

    detector.udp_dstmac = detector_configuration.get_detector_udp_dstmac()
    detector.udp_dstip  = detector_configuration.get_udp_dstip()
    detector.udp_dstport = detector_configuration.get_detector_port_first_module() # increments port by +1 for each module

    detector.udp_srcip = detector_configuration.get_detector_upd_ip()
    detector.udp_srcmac = detector_configuration.get_detector_udp_mac()

    detector.txdelay_frame = detector_configuration.get_detector_txndelay()
    detector.delay = detector_configuration.get_detector_delay()

    if detector_number == 2:
        detector.dacs.vb_comp = 1420

    if detector_number == 18:
        detector.dacs.vb_comp = 1320

    # workaround for mismatched frames problem
    if detector_number == 6:
        detector.sync = 1
        detector.setMaster(1, 31)

    # hardcoded fixed gain for specific modules
    if detector_number == 6:
        modules = [
            3, 4,
            6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
            23, 24
        ]
        detector.setGainMode(gainMode.FORCE_SWITCH_G1, modules)

    detector.temp_threshold = detector_configuration.get_detector_temp_threshold()
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



