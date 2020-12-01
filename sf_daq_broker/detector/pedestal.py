from slsdet import Jungfrau, detectorSettings
from time import sleep

def take_pedestal(detectors_name=[], rate=1):

    if len(detectors_name) < 1:
        return

    detectors_number = [int(detector_name[2:4]) for detector_name in detectors_name]

    detectors = [Jungfrau(detector_number) for detector_number in detectors_number]

    # reset bits
    for detector in detectors:
        detector.settings = detectorSettings.DYNAMICGAIN
    sleep(1)

    #HG0
    for detector in detectors:
        detector.settings = detectorSettings.DYNAMICHG0
    sleep(10*rate)

    #G0
    for detector in detectors:
        detector.settings = detectorSettings.DYNAMICGAIN
    sleep(10*rate)

    #G1
    for detector in detectors:
        detector.settings = detectorSettings.FORCESWITCHG1
    sleep(10*rate)

    #G2
    for detector in detectors:
        detector.settings = detectorSettings.FORCESWITCHG2
    sleep(10*rate)

    # reset bits
    for detector in detectors:
        detector.settings = detectorSettings.DYNAMICGAIN
    sleep(1)

    return
