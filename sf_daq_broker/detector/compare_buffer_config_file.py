import logging
import os

from sf_daq_broker.utils import json_load, json_save

from .detector_config import DetectorConfig, DETECTOR_DAQ


_logger = logging.getLogger("broker_writer")



def compare_buffer_config_file_all(overwrite_config=False):
    for detector_name in DETECTOR_DAQ:
        compare_buffer_config_file(detector_name, overwrite_config)


def compare_buffer_config_file(detector_name, overwrite_config=False):
    try:
        detector_configuration = DetectorConfig(detector_name)
    except RuntimeError as e:
        _logger.error(f"cannot configure detector {detector_name} (due to: {e})")
        return

    config_file = f"/gpfs/photonics/swissfel/buffer/config/{detector_name}.json"

    if not os.path.exists(config_file):
        _logger.error(f"{config_file} for {detector_name} does not exist")
        return

    parameters_file = json_load(config_file)

    parameters_current = {
        "detector_name":    detector_configuration.get_detector_name(),
        "n_modules":        detector_configuration.get_number_modules(),
        "streamvis_stream": detector_configuration.get_detector_daq_public_address(),
        "live_stream":      detector_configuration.get_detector_daq_data_address(),
        "start_udp_port":   detector_configuration.get_detector_port_first_module(),
        "buffer_folder":    f"/gpfs/photonics/swissfel/buffer/{detector_name}"
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



