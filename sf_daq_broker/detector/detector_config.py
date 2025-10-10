from sf_daq_broker.utils import json_load

from .detector_consts import BEAMLINE_DELAY, BEAMLINE_VLAN, DAQ_BEAMLINE, DAQ_MAC, DETECTOR_DAQ, DETECTOR_HOSTNAME, DETECTOR_TEMP_THRESHOLD, DETECTOR_TXNDELAY_FRAME


def make_udp_srcip(detectors, start=0):
    index = start
    res = {}
    for det in detectors:
        res[det] = index
        nmods = int(det[5:7])
        index += nmods
        if index > 256:
            raise ValueError(f"index {index} needed for {det} is outside the allowed range (<256)")
    return res

DETECTOR_NAMES = sorted(DETECTOR_HOSTNAME)
DETECTOR_UDP_SRCIP = make_udp_srcip(DETECTOR_NAMES, start=60)

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

        daq  = DETECTOR_DAQ[name]["daq"]
        port = DETECTOR_DAQ[name]["port"]

        if daq not in DAQ_MAC or port not in DAQ_MAC[daq]:
            raise_missing("DAQ/MAC")

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

        if name not in DETECTOR_TXNDELAY_FRAME:
            raise_missing("txndelay")

        txndelay = DETECTOR_TXNDELAY_FRAME[name]
        n_txndelay = len(txndelay)
        n_tiles = self.get_number_modules()

        if n_txndelay != n_tiles:
            raise RuntimeError(f"length {n_txndelay} of configured txndelay {txndelay} does not match number of tiles {n_tiles} of detector {name}")


#    def get_name(self):
#        return self.name

    def get_number(self):
        return int(self.name[2:4])

    def get_number_modules(self):
        return int(self.name[5:7])

    def get_size(self):
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
        daq  = DETECTOR_DAQ[self.name]["daq"]
        port = DETECTOR_DAQ[self.name]["port"]
        return DAQ_BEAMLINE[daq][port]


    def get_udp_dstip(self):
        vlan = self.get_vlan()
        daq = DETECTOR_DAQ[self.name]["daq"]
        return f"{vlan}.{daq}"

    def get_udp_dstmac(self):
        daq  = DETECTOR_DAQ[self.name]["daq"]
        port = DETECTOR_DAQ[self.name]["port"]
        return DAQ_MAC[daq][port]

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


    def get_txndelay(self):
        txndelay = {}
        for i in range(self.get_number_modules()):
            txndelay[i] = DETECTOR_TXNDELAY_FRAME[self.name][i]
        return txndelay


#    def get_daq_public_address(self):
#        ip   = self.get_daq_public_ip()
#        port = self.get_daq_public_port()
#        return f"tcp://{ip}:{port}"

#    def get_daq_public_ip(self):
#        daq = DETECTOR_DAQ[self.name]["daq"]
#        return DAQ_PUBLIC_IP[daq]

#    def get_daq_public_port(self):
#        return 9000 + self.get_number()


#    def get_daq_data_address(self):
#        ip   = self.get_daq_data_ip()
#        port = self.get_daq_data_port()
#        return f"tcp://{ip}:{port}"

#    def get_daq_data_ip(self):
#        daq = DETECTOR_DAQ[self.name]["daq"]
#        return DAQ_DATA_IP[daq]

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



