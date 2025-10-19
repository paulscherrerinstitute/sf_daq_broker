import logging
import os
from time import sleep


_logger = logging.getLogger("broker_writer")



def store_dap_info(beamline, pgroup, detector, start_pulse_id, stop_pulse_id, file_name_out):
    if None in (beamline, pgroup, detector, start_pulse_id, stop_pulse_id, file_name_out):
        msg = f"store_dap_info called with incomplete arguments: {beamline=}, {pgroup=}, {detector=}, {start_pulse_id=}, {stop_pulse_id=}, {file_name_out=}"
        _logger.error(msg)
        raise RuntimeError(msg)

    path_to_dap_files = f"/gpfs/photonics/swissfel/buffer/dap/data/{detector}"

    try:
        os.makedirs(path_to_dap_files, exist_ok=True)
    except Exception:
        _logger.exception(f"failed to create folder: {path_to_dap_files}")
        raise

    if not os.path.exists(path_to_dap_files):
        msg = f'DAP output directory "{path_to_dap_files}" is not reachable'
        _logger.error(msg)
        raise RuntimeError(msg)

    dap_endings = set(p // 10000 * 10000 for p in range(start_pulse_id, stop_pulse_id + 1))

    sleep(10)

    n_lines_out = 0

    with open(file_name_out, "w") as file_out:
        for dap_ending in dap_endings:
            dap_file_name = f"{path_to_dap_files}/{dap_ending}.dap"
            if not os.path.exists(dap_file_name):
                continue
            with open(dap_file_name, "r") as dap_file:
                all_lines = dap_file.read().splitlines()
                for line in all_lines:
                    pulse_id = int(line.split()[0])
                    if start_pulse_id <= pulse_id <= stop_pulse_id:
                        print(line, file=file_out)
                        n_lines_out += 1

    _logger.info(f"{n_lines_out} lines of DAP output stored to file {file_name_out}")



