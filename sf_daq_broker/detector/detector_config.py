import logging


_logger = logging.getLogger("broker_writer")

_beamline_vlan = {
    "alvra"       : "10.3.10",
    "bernina"     : "10.3.20",
    "cristallina" : "10.3.30",
    "furka"       : "10.3.50",
    "maloja"      : "10.3.40"
}

_daq_mac = {
    3  : {0: "98:f2:b3:d4:5f:d0", 1: "98:f2:b3:d4:5f:d1"},
    8  : {0: "b8:83:03:6e:de:9c", 1: "b8:83:03:6e:de:9d"},
    9  : {0: "04:09:73:dc:fa:18", 1: "04:09:73:dc:fa:19"},
    10 : {0: "88:e9:a4:1a:b1:a0", 1: "88:e9:a4:1a:b1:a1"},
    12 : {0: "88:e9:a4:6c:77:d0", 1: "88:e9:a4:6c:77:d1"},
    13 : {0: "88:e9:a4:3b:2c:d4", 1: "88:e9:a4:3b:2c:d5"}
}

_daq_beamline = {
    3  : {0: "alvra",   1: "bernina"},
    8  : {0: "alvra",   1: "cristallina"},
    9  : {0: "maloja",  1: "furka"},
    10 : {0: "bernina", 1: "cristallina"},
    12 : {0: "alvra",   1: "bernina"},
    13 : {0: "alvra",   1: "bernina"}
}

_daq_public_ip = {
    3  : "129.129.241.42",
    8  : "129.129.241.46",
    9  : "129.129.241.50",
    10 : "129.129.241.62",
    12 : "129.129.241.65",
    13 : "129.129.241.64"
}

_daq_data_ip = {
    3  : "192.168.30.29",
    8  : "192.168.30.8",
    9  : "192.168.30.25",
    10 : "192.168.30.11",
    12 : "192.168.30.38",
    13 : "192.168.30.39"
}

_beamline_delay = {
    "alvra"       : 0.000889,
    "bernina"     : 0.000890,
    "cristallina" : 0.000888,
    "furka"       : 0.004444,
    "maloja"      : 0.004444
}

_detector_hostname = {
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

_detector_names = {
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

_detector_daq = {
    "JF01T03V01" : { "daq" : 12, "port": 1},
    "JF02T09V03" : { "daq" : 12, "port": 0},
    "JF03T01V02" : { "daq" : 12, "port": 1},
    "JF04T01V01" : { "daq" : 12, "port": 1},
    "JF05T01V01" : { "daq" : 12, "port": 1},
    "JF06T08V04" : { "daq" : 13, "port": 0},
    "JF06T32V04" : { "daq" : 12, "port": 0},
    "JF07T32V02" : { "daq" : 13, "port": 1},
    "JF08T01V01" : { "daq" : 13, "port": 0},
    "JF09T01V01" : { "daq" : 13, "port": 0},
    "JF10T01V01" : { "daq" : 13, "port": 0},
    "JF11T04V01" : { "daq" : 13, "port": 0},
    "JF13T01V01" : { "daq" : 13, "port": 1},
    "JF14T01V01" : { "daq" : 13, "port": 1},
    "JF15T08V01" : { "daq" : 9,  "port": 0},
    "JF16T03V01" : { "daq" : 10, "port": 1},
    "JF17T16V01" : { "daq" : 10, "port": 1},
    "JF18T01V01" : { "daq" : 9,  "port": 1}
}

_detector_port = {
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

_detector_udp_srcip = {
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

_detector_udp_srcmac = {
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

_detector_txndelay_frame = {
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

_detector_temp_threshold = {
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



def detector_human_names():
    return _detector_names


def get_streamvis_address():
    address = {}
    for d in _detector_daq:
        detector_number = int(d[2:4])
        daq = _detector_daq[d]["daq"]
        address[d] = f"sf-daq-{daq}:{5000 + detector_number}"
    return address


def configured_detectors_for_beamline(beamline=None):
    detectors = []
    if beamline is None:
        return detectors

    for detector_name in _detector_daq:
        daq = _detector_daq[detector_name]["daq"]
        port = _detector_daq[detector_name]["port"]
        if daq in _daq_beamline and port in _daq_beamline[daq]:
            if _daq_beamline[daq][port] == beamline:
                detectors.append(detector_name)

    return detectors


def compare_buffer_config_file_all(overwrite_config=False):
    for detector_name in _detector_daq:
        compare_buffer_config_file(detector_name, overwrite_config)


def compare_buffer_config_file(detector_name=None, overwrite_config=False):
    import os
    from sf_daq_broker.utils import json_save, json_load

    detector_configuration = DetectorConfig(detector_name)
    if not detector_configuration.is_configuration_present():
        _logger.error(f"{detector_name}: No detector configuration present")
        return

    config_file = f"/gpfs/photonics/swissfel/buffer/config/{detector_name}.json"

    if not os.path.exists(config_file):
        _logger.error(f"{config_file} for {detector_name} does not exist")
        return

    parameters_file = json_load(config_file)

    parameters_current = {
        "detector_name": detector_configuration.get_detector_name(),
        "n_modules": detector_configuration.get_number_modules(),
        "streamvis_stream": f"tcp://{detector_configuration.get_detector_daq_public_ip()}:{detector_configuration.get_detector_daq_public_port()}",
        "live_stream": f"tcp://{detector_configuration.get_detector_daq_data_ip()}:{detector_configuration.get_detector_daq_data_port()}",
        "start_udp_port": detector_configuration.get_detector_port_first_module(),
        "buffer_folder": f"/gpfs/photonics/swissfel/buffer/{detector_name}"
    }

    need_change = False
    for p in parameters_current:
        if p not in parameters_file:
            _logger.error(f"{detector_name}: parameter {p} is not present in buffer configuration file")
            need_change = True
            continue
        if parameters_current[p] != parameters_file[p]:
            _logger.error(f"{detector_name}: parameter {p} different in current configuration {parameters_current[p]} compared to config file {parameters_file[p]}")
            need_change = True

    if need_change:
        _logger.warning(f"{detector_name}: buffer config file need a change")
        if overwrite_config:
            _logger.warning(f"{detector_name}: config file will be overwritten")
            parameters_file.update(parameters_current)
            json_save(parameters_file, config_file)



class DetectorConfig():

    def __init__(self, detector_name=None):
        self._initialised = False

        if detector_name is None:
            _logger.error("No detector name given")
            return

        self._detector_name = detector_name

        if detector_name not in _detector_hostname:
            _logger.error("hostname is not know for this detector")
            return

        if detector_name not in _detector_daq:
            _logger.error("daq server is not know for this detector")
            return

        daq = _detector_daq[self._detector_name]["daq"]
        port = _detector_daq[self._detector_name]["port"]
        if daq not in _daq_mac or port not in _daq_mac[daq]:
            _logger.error("daq/mac configuration is not known for this detector")
            return

        if daq not in _daq_beamline or port not in _daq_beamline[daq]:
            _logger.error("no association between detector and beamline.")
            return

        if daq not in _daq_public_ip or daq not in _daq_data_ip:
            _logger.error("configuration for daq (public or data ip) are missing")
            return

        if detector_name not in _detector_port:
            _logger.error("config port is not know for this detector")
            return

        if detector_name not in _detector_udp_srcip or detector_name not in _detector_udp_srcmac:
            _logger.error("srcip or srcmac configuration is not known for this detector")
            return

        if detector_name not in _detector_txndelay_frame or len(_detector_txndelay_frame[detector_name]) != int(detector_name[5:7]):
            _logger.error("txndelay for this detector is not configured or wrong")
            return

        if detector_name not in _detector_temp_threshold:
            _logger.error("temp_threshold is not know for this detector")
            return

        self._initialised = True


    def is_configuration_present(self):
        return self._initialised

    def get_detector_name(self):
        return self._detector_name

    def get_detector_beamline(self):
        daq = _detector_daq[self._detector_name]["daq"]
        port = _detector_daq[self._detector_name]["port"]
        return _daq_beamline[daq][port]

    def get_detector_number(self):
        return int(self._detector_name[2:4])

    def get_number_modules(self):
        return int(self._detector_name[5:7])

    def get_detector_size(self):
        return [1024, self.get_number_modules()*512]

    def get_detector_hostname(self):
        return _detector_hostname[self._detector_name]

    def get_detector_udp_dstmac(self):
        daq = _detector_daq[self._detector_name]["daq"]
        port = _detector_daq[self._detector_name]["port"]
        return _daq_mac[daq][port]

    def get_detector_daq_public_ip(self):
        daq = _detector_daq[self._detector_name]["daq"]
        return _daq_public_ip[daq]

    def get_detector_daq_public_port(self):
        return 9000 + self.get_detector_number()

    def get_detector_daq_data_ip(self):
        daq = _detector_daq[self._detector_name]["daq"]
        return _daq_data_ip[daq]

    def get_detector_daq_data_port(self):
        return 9100 + self.get_detector_number()

    def get_detector_vlan(self):
        return _beamline_vlan[self.get_detector_beamline()]

    def get_udp_dstip(self):
        vlan = self.get_detector_vlan()
        daq = _detector_daq[self._detector_name]["daq"]
        return f"{vlan}.{daq}"

    def get_detector_port_first_module(self):
        return _detector_port[self._detector_name]

    def get_detector_upd_ip(self):
        vlan = self.get_detector_vlan()
        udp_ip = {}
        for i in range(self.get_number_modules()):
            n = _detector_udp_srcip[self._detector_name] + i
            udp_ip[i] = f"{vlan}.{n}"
        return udp_ip

    def get_detector_udp_mac(self):
        udp_mac = {}
        for i in range(self.get_number_modules()):
            n = _detector_udp_srcmac[self._detector_name] + i
            ee = hex(n)[2:]
            udp_mac[i] = f"00:aa:bb:cc:dd:{ee}"
        return udp_mac

    def get_detector_txndelay(self):
        txndelay = {}
        for i in range(self.get_number_modules()):
            txndelay[i] = _detector_txndelay_frame[self._detector_name][i]
        return txndelay

    def get_detector_delay(self):
        return _beamline_delay[self.get_detector_beamline()]

    def get_detector_temp_threshold(self):
        return _detector_temp_threshold[self._detector_name]



