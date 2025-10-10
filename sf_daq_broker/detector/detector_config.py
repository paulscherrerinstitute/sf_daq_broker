from sf_daq_broker.utils import json_load, parse_det_name

from .detector_consts import BEAMLINE_DELAY, BEAMLINE_VLAN, DAQ_BEAMLINE, DAQ_MAC, DETECTOR_DAQ, DETECTOR_HOSTNAME, DETECTOR_TEMP_THRESHOLD, DETECTOR_TEMP_THRESHOLD_DEFAULT, DETECTOR_TXDELAY_FRAME


def make_udp_srcip(detectors, start=0):
    index = start
    res = {}
    for det in detectors:
        res[det] = index
        nmods = parse_det_name(det).T
        index += nmods
        if index > 256:
            raise ValueError(f"index {index} needed for {det} is outside the allowed range (<256)")
    return res

DETECTOR_NAMES = sorted(DETECTOR_HOSTNAME)
DETECTOR_UDP_SRCIP = make_udp_srcip(DETECTOR_NAMES, start=60)


for det in DETECTOR_NAMES:
    DETECTOR_TEMP_THRESHOLD.setdefault(det, DETECTOR_TEMP_THRESHOLD_DEFAULT)


# config files generated during deployment

try:
    DETECTOR_DESC = json_load("/home/dbe/service_configs/detector_descriptions.json")
except:
    DETECTOR_DESC = {}

try:
    DETECTOR_PORT = json_load("/home/dbe/service_configs/detector_start_udp_ports.json")
except:
    DETECTOR_PORT = {}



class DetectorConfig():

    def __init__(self, name):
        self.name = name

        if name is None:
            raise RuntimeError("no detector name given")

        # helper to ensure conistent error message
        def raise_missing(what):
            raise RuntimeError(f"{what} not configured for detector {name}")

        if name not in DETECTOR_HOSTNAME:
            raise_missing("hostname")

        if name not in DETECTOR_DAQ:
            raise_missing("DAQ server")

        self.daq  = daq  = DETECTOR_DAQ[name]["daq"]
        self.port = port = DETECTOR_DAQ[name]["port"]

        if daq not in DAQ_MAC or port not in DAQ_MAC[daq]:
            raise_missing("DAQ MAC")

        if daq not in DAQ_BEAMLINE or port not in DAQ_BEAMLINE[daq]:
            raise_missing("association to beamline")

#        if daq not in DAQ_PUBLIC_IP:
#            raise_missing("DAQ public IP")

#        if daq not in DAQ_DATA_IP:
#            raise_missing("DAQ data IP")

        if name not in DETECTOR_PORT:
            raise_missing("config port")

        if name not in DETECTOR_UDP_SRCIP:
            raise_missing("srcip")

#        if name not in DETECTOR_UDP_SRCMAC:
#            raise_missing("srcmac")

        if name not in DETECTOR_TEMP_THRESHOLD:
            raise_missing("temp_threshold")

        if name not in DETECTOR_TXDELAY_FRAME:
            raise_missing("txndelay")

        n_tiles = self.get_number_modules()

        hostnames = DETECTOR_HOSTNAME[name]
        n_hostnames = len(hostnames)
        if n_hostnames != n_tiles:
            raise RuntimeError(f"length {n_hostnames} of configured hostnames {hostnames} does not match number of tiles ({n_tiles}) of detector {name}")

        txndelays = DETECTOR_TXDELAY_FRAME[name]
        n_txndelays = len(txndelays)
        if n_txndelays != n_tiles:
            raise RuntimeError(f"length {n_txndelays} of configured txndelay {txndelays} does not match number of tiles ({n_tiles}) of detector {name}")


#    def get_name(self):
#        return self.name

    def get_number(self):
        return parse_det_name(self.name).ID

    def get_number_modules(self):
        return parse_det_name(self.name).T

    def get_detsize(self):
        return [1024, self.get_number_modules()*512]


    def get_delay(self):
        return BEAMLINE_DELAY[self.get_beamline()]

    def get_vlan(self):
        return BEAMLINE_VLAN[self.get_beamline()]


    def get_hostname(self):
        return DETECTOR_HOSTNAME[self.name]

    def get_port_first_module(self):
        return DETECTOR_PORT[self.name]

    def get_temp_threshold(self):
        return DETECTOR_TEMP_THRESHOLD[self.name]


    def get_beamline(self):
        return DAQ_BEAMLINE[self.daq][self.port]


    def get_udp_dstip(self):
        vlan = self.get_vlan()
        return f"{vlan}.{self.daq}"

    def get_udp_dstmac(self):
        return DAQ_MAC[self.daq][self.port]

    def get_udp_srcip(self):
        vlan = self.get_vlan()
        udp_ip = {}
        for i in range(self.get_number_modules()):
            n = DETECTOR_UDP_SRCIP[self.name] + i
            udp_ip[i] = f"{vlan}.{n}"
        return udp_ip

    def get_udp_srcmac(self):
        n = self.get_number()
        hn = hex(n)[2:]
        udp_mac = {}
        for i in range(self.get_number_modules()):
            hi = hex(i)[2:]
            udp_mac[i] = f"de:de:cd:aa:{hn}:{hi}"
        return udp_mac


    def get_txdelay_frame(self):
        txndelays = DETECTOR_TXDELAY_FRAME[self.name]
        return dict(enumerate(txndelays))


#    def get_daq_public_address(self):
#        ip   = self.get_daq_public_ip()
#        port = self.get_daq_public_port()
#        return f"tcp://{ip}:{port}"

#    def get_daq_public_ip(self):
#        return DAQ_PUBLIC_IP[self.daq]

#    def get_daq_public_port(self):
#        return 9000 + self.get_number()


#    def get_daq_data_address(self):
#        ip   = self.get_daq_data_ip()
#        port = self.get_daq_data_port()
#        return f"tcp://{ip}:{port}"

#    def get_daq_data_ip(self):
#        return DAQ_DATA_IP[self.daq]

#    def get_daq_data_port(self):
#        return 9100 + self.get_number()


    def __repr__(self):
        res = {}
        for name in dir(self):
            prefix = "get_"
            if name.startswith(prefix):
                func = getattr(self, name)
                value = func()
                name = name[len(prefix):]
                res[name] = value
        res = "\n".join(f"{k}: {v}" for k, v in sorted(res.items()))
        return res



