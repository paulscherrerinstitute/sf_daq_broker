import argparse
import os
from sls_detector import Eiger, Jungfrau

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--detector", default=None,               help="name of detector, e.g JF01T03V01")
    args = parser.parse_args()

    detector_name = args.detector

    if detector_name is None:
        print("No detector name given")
        exit()

    if detector_name[:2] != "JF":
        print(f'Not a Jungfrau detector name {detector_name}')
        exit()

    if len(detector_name) != 10:
        print(f'Not proper name of detector {detector_name}')
        exit()

    detector_number = int(detector_name[2:4])

    config_file = f'{detector_name}.config'

    if not os.path.exists(config_file):
        print(f'{config_file} for {detector_name} does not exists')
        exit()

    detector = Jungfrau(detector_number)
    
    detector.stop_detector()
    detector.free_shared_memory()
    detector.load_config(config_file)
    detector.power_chip = True
    detector.high_voltage = 120

if __name__ == "__main__":
    main()

