import logging


_logger = logging.getLogger("broker_writer")

BEAMLINE_VLAN = {
    "alvra"       : "10.3.10",
    "bernina"     : "10.3.20",
    "cristallina" : "10.3.30",
    "maloja"      : "10.3.40",
    "furka"       : "10.3.50"
}

DAQ_MAC = {
    3  : {0: "98:f2:b3:d4:5f:d0", 1: "98:f2:b3:d4:5f:d1"},
    8  : {0: "b8:83:03:6e:de:9c", 1: "b8:83:03:6e:de:9d"},
    9  : {0: "04:09:73:dc:fa:18", 1: "04:09:73:dc:fa:19"},
    10 : {0: "88:e9:a4:1a:b1:a0", 1: "88:e9:a4:1a:b1:a1"},
    12 : {0: "88:e9:a4:6c:77:d0", 1: "88:e9:a4:6c:77:d1"},
    13 : {0: "88:e9:a4:3b:2c:d4", 1: "88:e9:a4:3b:2c:d5"}
}

DAQ_BEAMLINE = {
    3  : {0: "alvra",   1: "bernina"},
    8  : {0: "alvra",   1: "cristallina"},
    9  : {0: "maloja",  1: "furka"},
    10 : {0: "bernina", 1: "cristallina"},
    12 : {0: "alvra",   1: "bernina"},
    13 : {0: "alvra",   1: "bernina"}
}

DAQ_PUBLIC_IP = {
    3  : "129.129.241.42",
    8  : "129.129.241.46",
    9  : "129.129.241.50",
    10 : "129.129.241.62",
    12 : "129.129.241.65",
    13 : "129.129.241.64"
}

DAQ_DATA_IP = {
    3  : "192.168.30.29",
    8  : "192.168.30.8",
    9  : "192.168.30.25",
    10 : "192.168.30.11",
    12 : "192.168.30.38",
    13 : "192.168.30.39"
}

BEAMLINE_DELAY = {
    "alvra"       : 0.000889,
    "bernina"     : 0.000890,
    "cristallina" : 0.000888,
    "maloja"      : 0.004444,
    "furka"       : 0.004444
}

DETECTOR_HOSTNAME = {
    "JF01T03V01" : ["JF1M5B-01", "JF1M5B-02", "JF1M5B-03"],
    "JF02T09V03" : ["JF4M5-01", "JF4M5-02", "JF4M5-03", "JF4M5-04", "JF4M5-05", "JF4M5-06", "JF4M5-07", "JF4M5-08", "JF4M5-09"],
    "JF03T01V02" : ["JF0M5B-I0-01"],
    "JF04T01V01" : ["jf0m5b-fl-01"],
    "JF05T01V01" : ["JF0M5B-ST-01"],
    "JF06T08V04" : ["jf16ma-07", "jf16ma-08", "jf16ma-11", "jf16ma-12", "jf16ma-15", "jf16ma-16", "jf16ma-19", "jf16ma-20"],
    "JF06T32V04" : ["Jf16ma-00", "jf16ma-01", "jf16ma-02", "jf16ma-03", "jf16ma-04", "jf16ma-05", "jf16mA-06", "jf16ma-07", "jf16ma-08", "jf16ma-09", "jf16ma-10", "jf16ma-11", "jf16ma-12", "jf16ma-13", "jf16ma-14", "jf16ma-15", "jf16ma-16", "jf16ma-17", "jf16ma-18", "jf16ma-19", "jf16ma-20", "jf16ma-21", "jf16ma-22", "jf16ma-23", "jf16ma-24", "jf16ma-25", "jf16ma-26", "jf16ma-27", "jf16ma-28", "jf16ma-29", "jf16ma-30", "jf16ma-31"],
    "JF07T32V02" : ["JF16MB-00", "JF16MB-01", "JF16MB-02", "JF16MB-03", "JF16MB-04", "JF16MB-05", "JF16MB-06", "JF16MB-07", "JF16MB-08", "JF16MB-09", "JF16MB-10", "JF16MB-11", "JF16MB-12", "JF16MB-13", "JF16MB-14", "JF16MB-15", "JF16MB-16", "JF16MB-17", "JF16MB-18", "JF16MB-19", "JF16MB-20", "JF16MB-21", "JF16MB-22", "JF16MB-23", "JF16MB-24", "JF16MB-25", "JF16MB-26", "JF16MB-27", "JF16MB-28", "JF16MB-29", "JF16MB-30", "JF16MB-31"],
    "JF08T01V01" : ["JF08T01V01"],
    "JF09T01V01" : ["JF09T01V01"],
    "JF10T01V01" : ["JF10T01V01"],
    "JF11T04V01" : ["bchip243", "bchip244", "bchip245", "bchip246"],
    "JF13T01V01" : ["JF13T01"],
    "JF14T01V01" : ["JF14T01"],
    "JF15T08V01" : ["JF4MG-0", "JF4MG-1", "JF4MG-2", "JF4MG-3", "JF4MG-4", "JF4MG-5", "JF4MG-6", "JF4MG-7"],
    "JF16T03V01" : ["JF16T03-0", "JF16T03-1", "JF16T03-2"],
    "JF17T16V01" : ["jf8MA-00", "jf8MA-01", "jf8MA-02", "jf8MA-03", "jf8MA-04", "jf8MA-05", "jf8MA-06", "jf8MA-07", "jf8MA-08", "jf8MA-09", "jf8MA-10", "jf8MA-11", "jf8MA-12", "jf8MA-13", "jf8MA-14", "jf8MA-15"],
    "JF18T01V01" : ["jf18T01-00"]
}

DETECTOR_NAMES = {
    "JF01T03V01" : "1p5M Bernina detector",
    "JF02T09V03" : "von Hamos 4.5M",
    "JF03T01V02" : "Bernina I0, 1 module",
    "JF04T01V01" : "Fluorescence, 1 module",
    "JF05T01V01" : "Stripsel, 1 module",
    "JF06T08V04" : "4M version of 16M detector",
    "JF06T32V04" : "16M detector",
    "JF07T32V02" : "16M detector",
    "JF08T01V01" : "Visual light detector, 1 module",
    "JF09T01V01" : "Flex, 1 module",
    "JF10T01V01" : "Flex-stripsel, 1 module",
    "JF11T04V01" : "TXS, 4 modules detector",
    "JF13T01V01" : "Vacuum detector",
    "JF14T01V01" : "RIXS detector",
    "JF15T08V01" : "Maloja, 8 modules detector, 4M",
    "JF16T03V01" : "Cristallina-Q, 3 modules detector, 1p5M",
    "JF17T16V01" : "Cristallina-MX, 16 modules detector, 8M",
    "JF18T01V01" : "Furka, RIXS detector"
}

DETECTOR_DAQ = {
    "JF01T03V01" : {"daq": 12, "port": 1},
    "JF02T09V03" : {"daq": 12, "port": 0},
    "JF03T01V02" : {"daq": 12, "port": 1},
    "JF04T01V01" : {"daq": 12, "port": 1},
    "JF05T01V01" : {"daq": 12, "port": 1},
    "JF06T08V04" : {"daq": 13, "port": 0},
    "JF06T32V04" : {"daq": 12, "port": 0},
    "JF07T32V02" : {"daq": 13, "port": 1},
    "JF08T01V01" : {"daq": 13, "port": 0},
    "JF09T01V01" : {"daq": 13, "port": 0},
    "JF10T01V01" : {"daq": 13, "port": 0},
    "JF11T04V01" : {"daq": 13, "port": 0},
    "JF13T01V01" : {"daq": 13, "port": 1},
    "JF14T01V01" : {"daq": 13, "port": 1},
    "JF15T08V01" : {"daq": 9,  "port": 0},
    "JF16T03V01" : {"daq": 10, "port": 1},
    "JF17T16V01" : {"daq": 10, "port": 1},
    "JF18T01V01" : {"daq": 9,  "port": 1}
}

DETECTOR_PORT = {
    "JF01T03V01" : 50010,
    "JF02T09V03" : 50020,
    "JF03T01V02" : 50030,
    "JF04T01V01" : 50040,
    "JF05T01V01" : 50050,
    "JF06T08V04" : 50060,
    "JF06T32V04" : 50060,
    "JF07T32V02" : 50100,
    "JF08T01V01" : 50140,
    "JF09T01V01" : 50150,
    "JF10T01V01" : 50160,
    "JF11T04V01" : 50170,
    "JF13T01V01" : 50190,
    "JF14T01V01" : 50191,
    "JF15T08V01" : 50192,
    "JF16T03V01" : 50200,
    "JF17T16V01" : 50203,
    "JF18T01V01" : 50219
}

DETECTOR_UDP_SRCIP = {
    "JF01T03V01" : 60,
    "JF02T09V03" : 65,
    "JF03T01V02" : 75,
    "JF04T01V01" : 76,
    "JF05T01V01" : 77,
    "JF06T08V04" : 78,
    "JF06T32V04" : 78,
    "JF07T32V02" : 101,
    "JF08T01V01" : 130,
    "JF09T01V01" : 131,
    "JF10T01V01" : 132,
    "JF11T04V01" : 133,
    "JF13T01V01" : 140,
    "JF14T01V01" : 141,
    "JF15T08V01" : 142,
    "JF16T03V01" : 150,
    "JF17T16V01" : 155,
    "JF18T01V01" : 171
}

DETECTOR_UDP_SRCMAC = {
    "JF01T03V01" : 16,
    "JF02T09V03" : 32,
    "JF03T01V02" : 42,
    "JF04T01V01" : 43,
    "JF05T01V01" : 44,
    "JF06T08V04" : 45,
    "JF06T32V04" : 45,
    "JF07T32V02" : 81,
    "JF08T01V01" : 121,
    "JF09T01V01" : 122,
    "JF10T01V01" : 123,
    "JF11T04V01" : 124,
    "JF13T01V01" : 131,
    "JF14T01V01" : 132,
    "JF15T08V01" : 133,
    "JF16T03V01" : 143,
    "JF17T16V01" : 148,
    "JF18T01V01" : 164
}

DETECTOR_TXNDELAY_FRAME = {
    "JF01T03V01" : [9, 9, 9],
    "JF02T09V03" : [7, 7, 7, 7, 8, 8, 8, 8, 9],
    "JF03T01V02" : [9],
    "JF04T01V01" : [8],
    "JF05T01V01" : [8],
    "JF06T08V04" : [0, 0, 1, 1, 2, 2, 3, 3],
    "JF06T32V04" : [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 9, 9, 9, 9],
    "JF07T32V02" : [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7],
    "JF08T01V01" : [8],
    "JF09T01V01" : [8],
    "JF10T01V01" : [8],
    "JF11T04V01" : [0, 1, 2, 3],
    "JF13T01V01" : [8],
    "JF14T01V01" : [8],
    "JF15T08V01" : [0, 0, 1, 1, 2, 2, 3, 3],
    "JF16T03V01" : [4, 5, 6],
    "JF17T16V01" : [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4],
    "JF18T01V01" : [0]
}

DETECTOR_TEMP_THRESHOLD = {
    "JF01T03V01" : 55,
    "JF02T09V03" : 45,
    "JF03T01V02" : 55,
    "JF04T01V01" : 55,
    "JF05T01V01" : 55,
    "JF06T08V04" : 48,
    "JF06T32V04" : 48,
    "JF07T32V02" : 55,
    "JF08T01V01" : 55,
    "JF09T01V01" : 55,
    "JF10T01V01" : 55,
    "JF11T04V01" : 55,
    "JF13T01V01" : 55,
    "JF14T01V01" : 55,
    "JF15T08V01" : 55,
    "JF16T03V01" : 55,
    "JF17T16V01" : 55,
    "JF18T01V01" : 55
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

        if daq not in DAQ_PUBLIC_IP:
            raise_missing("DAQ public IP")

        if daq not in DAQ_DATA_IP:
            raise_missing("DAQ data IP")

        if detector_name not in DETECTOR_PORT:
            raise_missing("config port")

        if detector_name not in DETECTOR_UDP_SRCIP:
            raise_missing("srcip")

        if detector_name not in DETECTOR_UDP_SRCMAC:
            raise_missing("srcmac")

        if detector_name not in DETECTOR_TEMP_THRESHOLD:
            raise_missing("temp_threshold")

        if detector_name not in DETECTOR_TXNDELAY_FRAME:
            raise_missing("txndelay")

        txndelay = DETECTOR_TXNDELAY_FRAME[detector_name]
        n_txndelay = len(txndelay)
        n_tiles = int(detector_name[5:7])

        if n_txndelay != n_tiles:
            raise RuntimeError(f"length {n_txndelay} of configured txndelay {txndelay} does not match number of tiles {n_tiles} of detector {detector_name}")


    def get_detector_name(self):
        return self._detector_name

    def get_detector_beamline(self):
        daq  = DETECTOR_DAQ[self._detector_name]["daq"]
        port = DETECTOR_DAQ[self._detector_name]["port"]
        return DAQ_BEAMLINE[daq][port]

    def get_detector_number(self):
        return int(self._detector_name[2:4])

    def get_number_modules(self):
        return int(self._detector_name[5:7])

    def get_detector_size(self):
        return [1024, self.get_number_modules()*512]

    def get_detector_hostname(self):
        return DETECTOR_HOSTNAME[self._detector_name]

    def get_detector_udp_dstmac(self):
        daq  = DETECTOR_DAQ[self._detector_name]["daq"]
        port = DETECTOR_DAQ[self._detector_name]["port"]
        return DAQ_MAC[daq][port]


    def get_detector_daq_public_address(self):
        ip   = self.get_detector_daq_public_ip()
        port = self.get_detector_daq_public_port()
        return f"tcp://{ip}:{port}"

    def get_detector_daq_public_ip(self):
        daq = DETECTOR_DAQ[self._detector_name]["daq"]
        return DAQ_PUBLIC_IP[daq]

    def get_detector_daq_public_port(self):
        return 9000 + self.get_detector_number()


    def get_detector_daq_data_address(self):
        ip   = self.get_detector_daq_data_ip()
        port = self.get_detector_daq_data_port()
        return f"tcp://{ip}:{port}"

    def get_detector_daq_data_ip(self):
        daq = DETECTOR_DAQ[self._detector_name]["daq"]
        return DAQ_DATA_IP[daq]

    def get_detector_daq_data_port(self):
        return 9100 + self.get_detector_number()


    def get_detector_vlan(self):
        return BEAMLINE_VLAN[self.get_detector_beamline()]

    def get_udp_dstip(self):
        vlan = self.get_detector_vlan()
        daq = DETECTOR_DAQ[self._detector_name]["daq"]
        return f"{vlan}.{daq}"

    def get_detector_port_first_module(self):
        return DETECTOR_PORT[self._detector_name]

    def get_detector_upd_ip(self):
        vlan = self.get_detector_vlan()
        udp_ip = {}
        for i in range(self.get_number_modules()):
            n = DETECTOR_UDP_SRCIP[self._detector_name] + i
            udp_ip[i] = f"{vlan}.{n}"
        return udp_ip

    def get_detector_udp_mac(self):
        udp_mac = {}
        for i in range(self.get_number_modules()):
            n = DETECTOR_UDP_SRCMAC[self._detector_name] + i
            ee = hex(n)[2:]
            udp_mac[i] = f"00:aa:bb:cc:dd:{ee}"
        return udp_mac

    def get_detector_txndelay(self):
        txndelay = {}
        for i in range(self.get_number_modules()):
            txndelay[i] = DETECTOR_TXNDELAY_FRAME[self._detector_name][i]
        return txndelay

    def get_detector_delay(self):
        return BEAMLINE_DELAY[self.get_detector_beamline()]

    def get_detector_temp_threshold(self):
        return DETECTOR_TEMP_THRESHOLD[self._detector_name]



