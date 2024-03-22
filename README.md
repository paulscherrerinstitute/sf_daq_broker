# Table of content
- [Table of content](#table-of-content)
- [SwissFEL DAQ Broker: SF-DAQ Component Overview](#swissfel-daq-broker-sf-daq-component-overview)
  - [Components of SF-DAQ](#components-of-sf-daq)
  - [Functionalities of sf-daq\_broker](#functionalities-of-sf-daq_broker)
- [Deployment](#deployment)
- [Communication with sf-daq\_broker](#communication-with-sf-daq_broker)
  - [Example1](#example1)
  - [Example2](#example2)
- [Directory Structure](#directory-structure)
- [Bookkeeping](#bookkeeping)
  
# SwissFEL DAQ Broker: SF-DAQ Component Overview

The SwissFEL DAQ Broker Component, (**sf-daq_broker**, serves as the primary user entry point into SF-DAQ (**sf-daq**). SF-DAQ consists of several integral components, including:

## Components of SF-DAQ

1. [sf_daq_buffer](https://github.com/paulscherrerinstitute/sf_daq_buffer)

   Responsible for writing/reading to/from the DetectorBuffer for Jungfrau detectors.

2. [data_api](https://github.com/paulscherrerinstitute/data_api_python)

    Retrieves data from Data-/Image- buffers, catering to BS- and Camera sources respectively.

3. [epics-buffer](https://github.com/paulscherrerinstitute/std_daq_service/tree/master/std_daq_service/epics) 

    Manages storing/retrieving Epics data.


## Functionalities of sf-daq_broker

The sf-daq_broker offers a range of functionalities that include:

  1. Data Retrieval
     * Accesses data from various buffers: data, image, detector, and Epics.

  2. Data Validation
     * Ensures retrieved data aligns with requested parameters.

  3. Configuration of Epics Buffers
     * Facilitates individual Epics buffer configuration for each beamline.

  4. Detector Power-On and Configuration
     * Manages the activation and setup of detectors associated with a specific beamline.

  5. Pedestal (Dark Run) Operations
     * Handles pedestal data acquisition and processing procedures.

  6. Provides ZeroMQ streams 
     * Offers ZeroMQ streams for [detector visualization](https://github.com/paulscherrerinstitute/streamvis) and the [Detector Analysis Pipeline(DAP)](https://gitlab.psi.ch/sf-daq/dap).

  7. Interface to [DAP](https://gitlab.psi.ch/sf-daq/dap) Configuration
     * Provides an interface to configure the Detector Analysis Pipeline(DAP).


The utilization of sf_daq_broker grants users access to a comprehensive suite of functionalities within SF-DAQ, empowering efficient data retrieval, configuration, and management for experiments conducted at SwissFEL.

# Deployment

The current deployment of sf_daq_broker at SwissFEL is executed using [ansible](https://git.psi.ch/swissfel/sf-daq_install).

# Communication with sf-daq_broker

Interaction with sf_daq_broker occurs through REST API calls, extensively detailed [here](broker_rest_api.md).

## Example1

A command-line example showcasing the usage of the broker to request data retrieval is [daq_client.py](client/daq_client.py). To execute, Python > 3.6 and standard packages (requests, os, json) are required. Utilizing the standard PSI Python environment suffices for this purpose:
```bash
$ module load psi-python39/2021.11 

$ python daq_client.py --help
usage: daq_client.py [-h] [-p PGROUP] [-c CHANNELS_FILE] [-e EPICS_FILE] [-f FILE_DETECTORS] [-r RATE_MULTIPLICATOR]
                     [-s SCAN_STEP_FILE] [--start_pulseid START_PULSEID] [--stop_pulseid STOP_PULSEID]

simple daq client example

optional arguments:
  -h, --help            show this help message and exit
  -p PGROUP, --pgroup PGROUP
                        pgroup, example p12345
  -c CHANNELS_FILE, --channels_file CHANNELS_FILE
                        TXT file with list channels
  -e EPICS_FILE, --epics_file EPICS_FILE
                        TXT file with list of epics channels to save
  -f FILE_DETECTORS, --file_detectors FILE_DETECTORS
                        JSON file with the detector list
  -r RATE_MULTIPLICATOR, --rate_multiplicator RATE_MULTIPLICATOR
                        rate multiplicator (1(default): 100Hz, 2: 50Hz,)
  -s SCAN_STEP_FILE, --scan_step_file SCAN_STEP_FILE
                        JSON file with the scan step information
  --start_pulseid START_PULSEID
                        start pulseid
  --stop_pulseid STOP_PULSEID
                        stop pulseid

``` 

## Example2

Another example presents a more start/stop-oriented data acquisition process. Alongside [daq_config.py](client/daq_client.py), the script [client_example.py](client/client_example.py) is required to run this example.
```bash
. /opt/gfa/python 3.9 # this loads proper environment with pyepics in it
$ ipython

In [1]: import client_example as client                                                                                                
In [2]: daq_client = client.BrokerClient(pgroup="p12345")                                                                                     
In [3]: daq_client.configure(channels_file="channel_list", rate_multiplicator=2, detectors_file="jf_jf01.json")                              

In [4]: daq_client.run(1000)                                                                                                
[####################] 99% Run: 2
success: run number(request_id) is 2
```

# Directory Structure

The structure where **sf-daq** stores data resides primarily in the **`/sf/{beamline}/data/{pgroup}/raw/`** directory. This structure adheres to a specific format:

* JF_pedestals/
  Contains Jungfrau pedestal files, both in raw and converted formats, along with gainMaps files for experiment-utilized detectors.

* runXXXX/
  Corresponds to the run (or scan) directory. In cases where a "user_tag" is added, the directory is named runXXXX-{user_tag}/.
  * data/
    Contains files formatted based on the sf-daq request.
  * meta/
    Holds JSON files with the request details for each acquisition step and a scan.json file that encapsulates the entire run/scan information.
  * logs/
    Houses log files from sf-daq writers, providing information regarding corresponding data retrieval actions.
  * raw_data/ (optional)
    Contains raw Jungfrau files, especially if different formats from raw files were requested by sf-daq.
  * aux/ (optional)
    Contains additional files.

File names within each acquisition step are prefixed with acqYYYY. to denote the acquisition step number. An example directory structure for a scan with multiple acquisition steps is provided below.
```bash
run0010/
├── data
│   ├── acq0001.BSDATA.h5
│   ├── acq0001.JF01T03V01.dap
│   ├── acq0001.JF01T03V01.h5
│   ├── acq0001.JF03T01V02.dap
│   ├── acq0001.JF03T01V02.h5
│   ├── acq0001.PVDATA.h5
│   ├── acq0002.BSDATA.h5
│   ├── acq0002.JF01T03V01.dap
│   ├── acq0002.JF01T03V01.h5
│   ├── acq0002.JF03T01V02.dap
│   ├── acq0002.JF03T01V02.h5
│   ├── acq0002.PVDATA.h5
├── logs
│   ├── acq0001.BSDATA.log
│   ├── acq0001.JF01T03V01.log
│   ├── acq0001.JF03T01V02.log
│   ├── acq0001.PVDATA.log
│   ├── acq0002.BSDATA.log
│   ├── acq0002.JF01T03V01.log
│   ├── acq0002.JF03T01V02.log
│   ├── acq0002.PVDATA.log
├── meta
│   ├── acq0001.json
│   ├── acq0002.json
│   └── scan.json
└── raw_data
    ├── acq0001.JF03T01V02.h5
    ├── acq0002.JF03T01V02.h5
```

# Bookkeeping
Upon a successful request accepted by the broker, all parameters utilized are saved within a `meta/` subdirectory related to the corresponding run/scan. These files are named `acqYYYY.json`.

 For instance:
```bash
$ pwd
/sf/cristallina/data/p21528/raw/run0001/meta
$ ls
acq0001.json  acq0003.json  acq0005.json  acq0007.json  acq0009.json  acq0011.json  acq0013.json
acq0002.json  acq0004.json  acq0006.json  acq0008.json  acq0010.json  acq0012.json  scan.json
$ cat acq0010.json
{
  "pgroup": "p21528",
  "rate_multiplicator": 1,
  "append_user_tag_to_data_dir": false,
  "user_tag": "test",
  "run_number": 1,
  "start_pulseid": 18940426916,
  "stop_pulseid": 18940427116,
  "detectors": {
    "JF16T03V01": {}
  },
  "channels_list": [
    "SARFE10-PBPG050:PHOTON-ENERGY-PER-PULSE-AVG",
    "SARFE10-PBIG050-EVR0:CALCI",
    ...<skipped>...
    "SAROP31-PBPS149:YPOS",
    "SAR-CVME-TIFALL6:EvtSet"
  ],
  "pv_list": [
    "SARFE10-PBPG050:PHOTON-ENERGY-PER-PULSE-US",
    "SARFE10-PBPG050:PHOTON-ENERGY-PER-PULSE-DS",
    "SARFE10-OAPU044:MOTOR_X",
    ...<skipped>...
    "SAROP31-OKBH154:TX2.RBV"
  ],
  "beamline": "cristallina",
  "acquisition_number": 10,
  "request_time": "2023-09-05 15:28:24.291760",
  "unique_acquisition_run_number": 10
}
``` 
 Additionally, logs within the logs/ directory capture the output of retrieve actions by corresponding writers:
```bash
$ pwd
/sf/cristallina/data/p21528/raw/run0001/logs
$ ls
acq0001.BSDATA.log      acq0004.JF16T03V01.log  acq0007.PVDATA.log      acq0011.BSDATA.log
...

$ cat acq0010.BSDATA.log 
Request for data3buffer : output_file /sf/cristallina/data/p21528/raw/run0001/data/acq0010.BSDATA.h5 from pulse_id 18940426916 to 18940427116
Sleeping for 59.997645139694214 seconds before continuing.
Starting payload.
Using data_api3 databuffer writer.
data api 3 reader 0.8.8
Data download and writing took 2.8266358375549316 seconds.
...<skipped>...
check SAROP31-PBPS149:YPOS number of pulse_id(unique) is different from expected : 181 vs 201
check SAR-CVME-TIFALL6:EvtSet not present in file
Check of data consistency took 0.017050504684448242 seconds.
Finished. Took 18.1561918258667 seconds to complete request.

$ cat acq0010.PVDATA.log 
[sf.cristallina.epics_writer] Processing of b4396eec-4156-4ad1-b2da-62d903405ace started in service sf.cristallina.epics_writer.
[sf.cristallina.epics_writer] Requesting file /sf/cristallina/data/p21528/raw/run0001/data/acq0010.PVDATA.h5 for pulse_id range 18940426916 to 18940427116 with 132 channels.
[sf.cristallina.epics_writer] Request b4396eec-4156-4ad1-b2da-62d903405ace completed in 0.29 seconds.
[sf.cristallina.epics_writer] Output file analysis:
    [SARFE10-PBPG050:PHOTON-ENERGY-PER-PULSE-US] Point count 3 (1[2)0)
    [SARFE10-PBPG050:PHOTON-ENERGY-PER-PULSE-DS] Point count 3 (1[2)0)
    [SARFE10-OAPU044:MOTOR_X] Point count 1 (1[0)0)
    ...<skipped>...
    [SAROP31-OKBH154:TX2.RBV] Point count 1 (1[0)0)

$ cat acq0010.JF16T03V01.log 
Request for detector_buffer : output_file /sf/cristallina/data/p21528/raw/run0001/data/acq0010.JF16T03V01.h5 from pulse_id 18940426916 to 18940427116
Sleeping for 9.99739956855774 seconds before continuing.
Starting payload.
Using detector retrieve writer.
Starting detector retrieve from buffer /home/dbe/bin/sf_writer /sf/cristallina/data/p21528/raw/run0001/data/acq0010.JF16T03V01.h5 /gpfs/photonics/swissfel/buffer/JF16T03V01 3 18940426916 18940427116 1 
Retrieve Time : 0.33776354789733887
Finished retrieve from the buffer
Finished. Took 0.3386099338531494 seconds to complete request.
```

These logs provide insights such as missing pulseid, incomplete data for certain sources, and details about the consistency of the acquired data.

