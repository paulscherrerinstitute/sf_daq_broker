from sf_daq_broker.utils import json_load


BEAMLINE_VLAN = {
    "alvra"       : "10.3.10",
    "bernina"     : "10.3.20",
    "cristallina" : "10.3.30",
    "maloja"      : "10.3.40",
    "furka"       : "10.3.50"
}

DAQ_MAC = {
#    3  : {0: "98:f2:b3:d4:5f:d0", 1: "98:f2:b3:d4:5f:d1"},
#    8  : {0: "b8:83:03:6e:de:9c", 1: "b8:83:03:6e:de:9d"},
    9  : {0: "04:09:73:dc:fa:18", 1: "04:09:73:dc:fa:19"},
    10 : {0: "88:e9:a4:1a:b1:a0", 1: "88:e9:a4:1a:b1:a1"},
    12 : {0: "88:e9:a4:6c:77:d0", 1: "88:e9:a4:6c:77:d1"},
    13 : {0: "88:e9:a4:3b:2c:d4", 1: "88:e9:a4:3b:2c:d5"}
}

DAQ_BEAMLINE = {
#    3  : {0: "alvra",   1: "bernina"},
#    8  : {0: "alvra",   1: "cristallina"},
    9  : {0: "maloja",  1: "furka"},
    10 : {0: "bernina", 1: "cristallina"},
    12 : {0: "alvra",   1: "bernina"},
    13 : {0: "alvra",   1: "bernina"}
}

#DAQ_PUBLIC_IP = {
#    3  : "129.129.241.42",
#    8  : "129.129.241.46",
#    9  : "129.129.241.50",
#    10 : "129.129.241.62",
#    12 : "129.129.241.65",
#    13 : "129.129.241.64"
#}

#DAQ_DATA_IP = {
#    3  : "192.168.30.29",
#    8  : "192.168.30.8",
#    9  : "192.168.30.25",
#    10 : "192.168.30.11",
#    12 : "192.168.30.38",
#    13 : "192.168.30.39"
#}

BEAMLINE_DELAY = {
    "alvra"       : 0.000889,
    "bernina"     : 0.000890,
    "cristallina" : 0.000888,
    "maloja"      : 0.004444,
    "furka"       : 0.004444
}

DETECTOR_HOSTNAME = {
    "JF01T03V01" : ["jf1m5b-01", "jf1m5b-02", "jf1m5b-03"],
    "JF02T09V03" : ["jf4m5-01", "jf4m5-02", "jf4m5-03", "jf4m5-04", "jf4m5-05", "jf4m5-06", "jf4m5-07", "jf4m5-08", "jf4m5-09"],
    "JF03T01V02" : ["jf0m5b-i0-01"],
    "JF04T01V01" : ["jf0m5b-fl-01"],
    "JF05T01V01" : ["jf0m5b-st-01"],
    "JF06T08V07" : ["jf16ma-07", "jf16ma-08", "jf16ma-11", "jf16ma-12", "jf16ma-15", "jf16ma-16", "jf16ma-19", "jf16ma-20"],
    "JF06T32V07" : ["jf16ma-00", "jf16ma-01", "jf16ma-02", "jf16ma-03", "jf16ma-04", "jf16ma-05", "jf16ma-06", "jf16ma-07", "jf16ma-08", "jf16ma-09", "jf16ma-10", "jf16ma-11", "jf16ma-12", "jf16ma-13", "jf16ma-14", "jf16ma-15", "jf16ma-16", "jf16ma-17", "jf16ma-18", "jf16ma-19", "jf16ma-20", "jf16ma-21", "jf16ma-22", "jf16ma-23", "jf16ma-24", "jf16ma-25", "jf16ma-26", "jf16ma-27", "jf16ma-28", "jf16ma-29", "jf16ma-30", "jf16ma-31"],
    "JF07T32V02" : ["jf16mb-00", "jf16mb-01", "jf16mb-02", "jf16mb-03", "jf16mb-04", "jf16mb-05", "jf16mb-06", "jf16mb-07", "jf16mb-08", "jf16mb-09", "jf16mb-10", "jf16mb-11", "jf16mb-12", "jf16mb-13", "jf16mb-14", "jf16mb-15", "jf16mb-16", "jf16mb-17", "jf16mb-18", "jf16mb-19", "jf16mb-20", "jf16mb-21", "jf16mb-22", "jf16mb-23", "jf16mb-24", "jf16mb-25", "jf16mb-26", "jf16mb-27", "jf16mb-28", "jf16mb-29", "jf16mb-30", "jf16mb-31"],
    "JF08T01V01" : ["jf08t01v01"],
    "JF09T01V01" : ["jf09t01v01"],
    "JF10T01V01" : ["jf10t01v01"],
    "JF11T04V01" : ["bchip243", "bchip244", "bchip245", "bchip246"],
    "JF13T01V01" : ["jf13t01"],
    "JF14T01V01" : ["jf14t01"],
    "JF15T08V01" : ["jf4mg-0", "jf4mg-1", "jf4mg-2", "jf4mg-3", "jf4mg-4", "jf4mg-5", "jf4mg-6", "jf4mg-7"],
    "JF16T03V02" : ["jf16t03-0", "jf16t03-1", "jf16t03-2"],
    "JF17T16V01" : ["jf8ma-00", "jf8ma-01", "jf8ma-02", "jf8ma-03", "jf8ma-04", "jf8ma-05", "jf8ma-06", "jf8ma-07", "jf8ma-08", "jf8ma-09", "jf8ma-10", "jf8ma-11", "jf8ma-12", "jf8ma-13", "jf8ma-14", "jf8ma-15"],
    "JF18T01V01" : ["jf18t01-00"],
    "JF19T01V01" : ["jf19-00"],
    "JF20T01V01" : ["jf20-00"]
}

DETECTOR_NAMES = sorted(DETECTOR_HOSTNAME)

#DETECTOR_DESC = {
#    "JF01T03V01" : "Bernina (1.5M)",
#    "JF02T09V03" : "Alvra: von Hamos (4.5M)",
#    "JF03T01V02" : "Bernina: I0 (0.5M)",
#    "JF04T01V01" : "Bernina: Fluorescence (0.5M)",
#    "JF05T01V01" : "Cristallina: Stripsel (0.5M)",
#    "JF06T08V07" : "Alvra: 4M version of 16M (4M)",
#    "JF06T32V07" : "Alvra (16M)",
#    "JF07T32V02" : "Bernina (16M)",
#    "JF08T01V01" : "Alvra: Visual Light (0.5M)",
#    "JF09T01V01" : "Alvra: Flex (0.5M)",
#    "JF10T01V01" : "Alvra: Flex-Stripsel (0.5M)",
#    "JF11T04V01" : "Alvra: TXS (2M)",
#    "JF13T01V01" : "Bernina: Vacuum (0.5M)",
#    "JF14T01V01" : "Bernina: RIXS (0.5M)",
#    "JF15T08V01" : "Maloja (4M)",
#    "JF16T03V02" : "Cristallina-Q (1.5M)",
#    "JF17T16V01" : "Cristallina-MX (8M)",
#    "JF18T01V01" : "Furka: RIXS (0.5M)",
#    "JF19T01V01" : "Furka: UHV (0.5M)",
#    "JF20T01V01" : "Cristallina-Q: I0 (0.5M)"
#}

# config file generated during deployment
try:
    DETECTOR_DESC = json_load("/home/dbe/service_configs/detector_descriptions.json")
except:
    DETECTOR_DESC = {}

DETECTOR_DAQ = {
    "JF01T03V01" : {"daq": 12, "port": 1},
    "JF02T09V03" : {"daq": 12, "port": 0},
    "JF03T01V02" : {"daq": 12, "port": 1},
    "JF04T01V01" : {"daq": 12, "port": 1},
    "JF05T01V01" : {"daq": 10, "port": 1},
    "JF06T08V07" : {"daq": 12, "port": 0},
    "JF06T32V07" : {"daq": 12, "port": 0},
    "JF07T32V02" : {"daq": 13, "port": 1},
    "JF08T01V01" : {"daq": 13, "port": 0},
    "JF09T01V01" : {"daq": 13, "port": 0},
    "JF10T01V01" : {"daq": 13, "port": 0},
    "JF11T04V01" : {"daq": 13, "port": 0},
    "JF13T01V01" : {"daq": 13, "port": 1},
    "JF14T01V01" : {"daq": 13, "port": 1},
    "JF15T08V01" : {"daq": 9,  "port": 0},
    "JF16T03V02" : {"daq": 10, "port": 1},
    "JF17T16V01" : {"daq": 10, "port": 1},
    "JF18T01V01" : {"daq": 9,  "port": 1},
    "JF19T01V01" : {"daq": 9,  "port": 1},
    "JF20T01V01" : {"daq": 10, "port": 1}
}

#DETECTOR_PORT = {
#    "JF01T03V01" : 50100,
#    "JF02T09V03" : 50200,
#    "JF03T01V02" : 50300,
#    "JF04T01V01" : 50400,
#    "JF05T01V01" : 50500,
#    "JF06T08V07" : 50600,
#    "JF06T32V07" : 51200,
#    "JF07T32V02" : 50700,
#    "JF08T01V01" : 50800,
#    "JF09T01V01" : 50900,
#    "JF10T01V01" : 51000,
#    "JF11T04V01" : 51100,
#    "JF13T01V01" : 51300,
#    "JF14T01V01" : 51400,
#    "JF15T08V01" : 51500,
#    "JF16T03V02" : 51600,
#    "JF17T16V01" : 51700,
#    "JF18T01V01" : 51800,
#    "JF19T01V01" : 51900,
#    "JF20T01V01" : 52000
#}

# config file generated during deployment
try:
    DETECTOR_PORT = json_load("/home/dbe/service_configs/detector_start_udp_ports.json")
except:
    DETECTOR_PORT = {}

DETECTOR_UDP_SRCIP = {
    "JF01T03V01" : 60,
    "JF02T09V03" : 65,
    "JF03T01V02" : 75,
    "JF04T01V01" : 76,
    "JF05T01V01" : 77,
    "JF06T08V07" : 78,
    "JF06T32V07" : 78,
    "JF07T32V02" : 101,
    "JF08T01V01" : 130,
    "JF09T01V01" : 131,
    "JF10T01V01" : 132,
    "JF11T04V01" : 133,
    "JF13T01V01" : 140,
    "JF14T01V01" : 141,
    "JF15T08V01" : 142,
    "JF16T03V02" : 150,
    "JF17T16V01" : 155,
    "JF18T01V01" : 171,
    "JF19T01V01" : 172,
    "JF20T01V01" : 173
}

#DETECTOR_UDP_SRCMAC = {
#    "JF01T03V01" : 16,
#    "JF02T09V03" : 32,
#    "JF03T01V02" : 42,
#    "JF04T01V01" : 43,
#    "JF05T01V01" : 44,
#    "JF06T08V07" : 45,
#    "JF06T32V07" : 45,
#    "JF07T32V02" : 81,
#    "JF08T01V01" : 121,
#    "JF09T01V01" : 122,
#    "JF10T01V01" : 123,
#    "JF11T04V01" : 124,
#    "JF13T01V01" : 131,
#    "JF14T01V01" : 132,
#    "JF15T08V01" : 133,
#    "JF16T03V02" : 143,
#    "JF17T16V01" : 148,
#    "JF18T01V01" : 164,
#    "JF19T01V01" : 165,
#    "JF20T01V01" : 166
#}

DETECTOR_TXNDELAY_FRAME = {
    "JF01T03V01" : [9, 9, 9],
    "JF02T09V03" : [7, 7, 7, 7, 8, 8, 8, 8, 9],
    "JF03T01V02" : [9],
    "JF04T01V01" : [8],
    "JF05T01V01" : [8],
    "JF06T08V07" : [0, 0, 1, 1, 2, 2, 3, 3],
    "JF06T32V07" : [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 9, 9, 9, 9],
    "JF07T32V02" : [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7],
    "JF08T01V01" : [8],
    "JF09T01V01" : [8],
    "JF10T01V01" : [8],
    "JF11T04V01" : [0, 1, 2, 3],
    "JF13T01V01" : [8],
    "JF14T01V01" : [8],
    "JF15T08V01" : [0, 0, 1, 1, 2, 2, 3, 3],
    "JF16T03V02" : [4, 5, 6],
    "JF17T16V01" : [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4],
    "JF18T01V01" : [0],
    "JF19T01V01" : [0],
    "JF20T01V01" : [0]
}

DETECTOR_TEMP_THRESHOLD = {
    "JF01T03V01" : 55,
    "JF02T09V03" : 45,
    "JF03T01V02" : 55,
    "JF04T01V01" : 55,
    "JF05T01V01" : 55,
    "JF06T08V07" : 48,
    "JF06T32V07" : 48,
    "JF07T32V02" : 55,
    "JF08T01V01" : 55,
    "JF09T01V01" : 55,
    "JF10T01V01" : 55,
    "JF11T04V01" : 55,
    "JF13T01V01" : 55,
    "JF14T01V01" : 55,
    "JF15T08V01" : 55,
    "JF16T03V02" : 55,
    "JF17T16V01" : 55,
    "JF18T01V01" : 55,
    "JF19T01V01" : 55,
    "JF20T01V01" : 55
}



class DetectorConfig():

    def __init__(self, detector_name):
        self._detector_name = detector_name

        if detector_name is None:
            raise RuntimeError("no detector name given")

        # helper to ensure conistent error message
        def raise_missing(what):
            raise RuntimeError(f"{what} not configured for detector {detector_name}")

        if detector_name not in DETECTOR_HOSTNAME:
            raise_missing("hostname")

        if detector_name not in DETECTOR_DAQ:
            raise_missing("DAQ server")

        daq  = DETECTOR_DAQ[detector_name]["daq"]
        port = DETECTOR_DAQ[detector_name]["port"]

        if daq not in DAQ_MAC or port not in DAQ_MAC[daq]:
            raise_missing("DAQ/MAC")

        if daq not in DAQ_BEAMLINE or port not in DAQ_BEAMLINE[daq]:
            raise_missing("association to beamline")

#        if daq not in DAQ_PUBLIC_IP:
#            raise_missing("DAQ public IP")

#        if daq not in DAQ_DATA_IP:
#            raise_missing("DAQ data IP")

        if detector_name not in DETECTOR_PORT:
            raise_missing("config port")

        if detector_name not in DETECTOR_UDP_SRCIP:
            raise_missing("srcip")

#        if detector_name not in DETECTOR_UDP_SRCMAC:
#            raise_missing("srcmac")

        if detector_name not in DETECTOR_TEMP_THRESHOLD:
            raise_missing("temp_threshold")

        if detector_name not in DETECTOR_TXNDELAY_FRAME:
            raise_missing("txndelay")

        txndelay = DETECTOR_TXNDELAY_FRAME[detector_name]
        n_txndelay = len(txndelay)
        n_tiles = int(detector_name[5:7])

        if n_txndelay != n_tiles:
            raise RuntimeError(f"length {n_txndelay} of configured txndelay {txndelay} does not match number of tiles {n_tiles} of detector {detector_name}")


#    def get_name(self):
#        return self._detector_name

    def get_beamline(self):
        daq  = DETECTOR_DAQ[self._detector_name]["daq"]
        port = DETECTOR_DAQ[self._detector_name]["port"]
        return DAQ_BEAMLINE[daq][port]

    def get_number(self):
        return int(self._detector_name[2:4])

    def get_number_modules(self):
        return int(self._detector_name[5:7])

    def get_size(self):
        return [1024, self.get_number_modules()*512]

    def get_hostname(self):
        return DETECTOR_HOSTNAME[self._detector_name]

    def get_udp_dstmac(self):
        daq  = DETECTOR_DAQ[self._detector_name]["daq"]
        port = DETECTOR_DAQ[self._detector_name]["port"]
        return DAQ_MAC[daq][port]


#    def get_daq_public_address(self):
#        ip   = self.get_daq_public_ip()
#        port = self.get_daq_public_port()
#        return f"tcp://{ip}:{port}"

#    def get_daq_public_ip(self):
#        daq = DETECTOR_DAQ[self._detector_name]["daq"]
#        return DAQ_PUBLIC_IP[daq]

#    def get_daq_public_port(self):
#        return 9000 + self.get_number()


#    def get_daq_data_address(self):
#        ip   = self.get_daq_data_ip()
#        port = self.get_daq_data_port()
#        return f"tcp://{ip}:{port}"

#    def get_daq_data_ip(self):
#        daq = DETECTOR_DAQ[self._detector_name]["daq"]
#        return DAQ_DATA_IP[daq]

#    def get_daq_data_port(self):
#        return 9100 + self.get_number()


    def get_vlan(self):
        return BEAMLINE_VLAN[self.get_beamline()]

    def get_udp_dstip(self):
        vlan = self.get_vlan()
        daq = DETECTOR_DAQ[self._detector_name]["daq"]
        return f"{vlan}.{daq}"

    def get_port_first_module(self):
        return DETECTOR_PORT[self._detector_name]

    def get_udp_srcip(self):
        vlan = self.get_vlan()
        udp_ip = {}
        for i in range(self.get_number_modules()):
            n = DETECTOR_UDP_SRCIP[self._detector_name] + i
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
            txndelay[i] = DETECTOR_TXNDELAY_FRAME[self._detector_name][i]
        return txndelay

    def get_delay(self):
        return BEAMLINE_DELAY[self.get_beamline()]

    def get_temp_threshold(self):
        return DETECTOR_TEMP_THRESHOLD[self._detector_name]

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



