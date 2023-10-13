# SwissFEL DAQ Broker Component of SF_DAQ

This is part of [SF_DAQ](https://github.com/paulscherrerinstitute/sf_daq_buffer)

With move of detector to a buffer solution, the whole concept of data acquisition 
is reduced to reitrieve request from the buffers (data buffer for BS, image buffer for
the camera images, detector buffer for Jungfrau and epics PV's from epics service of std-daq)

# Table of content
1. [Call to broker](#call_broker)
    1. [Call](#call)
    2. [Parameters](#parameters)
    3. [Bookkeeping](#bookkeeping)
2. [Example1](#example1)
3. [Example2](#example2)
5. [Deployment](#deployment)

<a id="call_broker"></a>
## Call to broker

Current broker is running on single sf-daq server and serves for the whole Swissfel (Alva, Bernina, Cristallina, Furka, Maloja). 

<a id="call"></a>
### Call

The following code is enough to make a call to current broker:
```python
import requests
broker_address = "http://sf-daq:10002"
TIMEOUT_DAQ = 10

r = requests.post(f'{broker_address}/retrieve_from_buffers',json=parameters, timeout=TIMEOUT_DAQ)
```

return object `r` is a dictionary with at least two keys: `'status'` and `'message'`. In case of no problem with the request to retrieve data (so request is accepted to be processed
by broker), `'status'` is 'ok', `'message'` is 'OK' and there are additional fields in reply : `run_number`, `acquisition_number` and `unique_acquistition_number` and list of `'files'` which sf-daq will produce in corresponding data/ directory 
```python
r.json()
{'status': 'ok', 'message': 'OK', 'run_number': '10', 'acquisition_number': '1', 'unique_acquisition_number': '101', 'files': ['/sf/alvra/data/p17502/raw/run0010/data/acq0001.PVDATA.h5']}
```
In case of problem with the request or internal problems of sf-daq, `'status'` will be 'failed' and `'message'` field will contain an error description. 
``` python
r.json()
{'status': 'failed', 'message': 'pgroup directory /sf/alvra/data/p17500/raw/ not reachable'}
```

<a id="parameters"></a>
### Parameters
'parameters' passed in request is a dictionary.
There are very little number of mandatory key/values which needs to be present in the 'parameters' request, namely:
```
parameters["pgroup"] = "p12345"
parameters["start_pulseid"] = 1000 
parameters["stop_pulseid"]  = 2000 
```
 Failure to not provide one of these parameters will result in decline of the broker to retrieve data

 And number of optional parameters:
- "run_number" : integer positive number, indicates that current acquisition is a part of the scan. If not provided - new run_number is generated and returned (so can be used in following calls to sf-daq, if that was a first scan step)
- "append_user_tag_to_data_dir" : bool, append "user_tag" to run directory name, defaults False
- "user_tag" : string, with the user defined name to append to run directory (allowed characters are ascii symbols(lower/upper), digits and few special characters: "\_", "-", "+" and ".". In case "user_tag" contains other characters, they will be replaced by underscore symbol "_")
- "rate_multiplicator" : integer number, indicating what is the beam rate (or expectation for the source rate delivery), default is 1(means 100Hz), (2 - 50Hz, 4 - 25Hz; 10 - 10Hz, 20 - 5Hz, 100 - 1Hz). Currently setting or not this variable doesn't change anything in retrieve, but helps with the checks of the retrieve, see below
- "channels_list" : python list with the source name from data buffer (not CAMERA's images, theuy go to "camera_list")
- "camera_list" : python list with name of CAMERA's (complete name, with :FPICTURE at the end)
- "pv_list" : python list with name of epics PV to retrieve from archiver by cadump
- "detectors" : python dictionary, containing name of jungfrau detector (e.g. JF01T03V01) as key and a dictionary with parameters as a value, see [Detector parameters](#detector_parameters) for available options
- "scan_info" : python dictionary to specify that this request belongs to a particular scan (if proper information is provided (for example see scan_step.json in this directory), the appropriate scan_info json file will be created inside run directory)

 Successful request needs to have at least one list non-empty in request (otherwise there is nothing to ask to retrieve)

<a id="detector_parameters"></a>
#### Detector parameters
- `compression (bool)`: apply bitshuffle+lz4 compression, defaults to False
- `adc_to_energy (bool)`: apply gain and pedestal corrections, converting raw detector values into energy, defaults to False

The following parameters apply only when `conversion = True`, otherwise they are ignored:
- `mask (bool)`: perform masking of bad pixels (assign them to 0), defaults to True
- `double_pixels_action (str)`: what to do with double pixels at chip inner edges - "keep", "mask" or "interp" ("interp" is only possible when `gap_pixels = True` and not supported for 'factor'), defaults to "mask"
- `geometry (bool)`: apply geometry correction, defaults to False
- `gap_pixels (bool)`: add gap pixels between detector chips, defaults to True
- `factor (float, None)`: divide all pixel values by a factor and round the result, saving them as int32, keep the original values and type if None, defaults to None
- `disabled_modules (list(int))`: list of modules to disabled (not output) for the detector, defaults to empty list
- `roi (tuple or dictionary)`: roi's to output from the detector image; format is either tuple of tuples with roi coordinates (bottom, top, left, right) or dictionary with roi name and tuple of roi coordinates, defaults to None
- `downsample (tuple(int N,int M))`: reduce image using NxM pixels block, summing up pixels intensity, defaults to None or (1,1)
- `save_dap_results (bool)`: save results from dap processing(in case dap is running for that detector), defaults to False
- `selected_pulse_ids (list(int))`: output only pulseids present in the list (within the start_pulseid/stop_pulseid region), defaults to empty list(all pulseids)
- `save_ppicker_events_only (bool)`: within the start_pulseid/stop_pulsid region output only detector frames with pulse picker open, default to False

<a id="directory_structure"></a>
### Directory structure

sf-daq outputs data in raw/ folder of corresponding beamline and pgroup (/sf/{beamline}/data/{pgroup}/raw).
Directory structure is fixed to the following format:
* `JF_pedestals/` directory containing Jungfrau pedestal files (raw/ and converted to the pedestal values) as well as gainMaps files for the detectors used in experiment
* `runXXXX/` directory containing files related to the run(scan), where XXXX is the `run_number`. In case of "user_tag" addition, this directory wil be named `runXXXX-{user_tag}/`
* `runXXXX/data/` directory contains files in the format specified in request to sf-daq
* `runXXXX/meta/` directory contains json files with the request to sf-daq for each of the acquisition step and scan.json file which describes the whole run/scan
* `runXXXX/logs/` directory contains logs files from sf-daq with information from corresponding sf-daq writers
* `runXXXX/raw_data/` (optional) directory contains raw Jungfrau files, in case if different from raw format files were requested to sf-daq
* `runXXXX/aux/` (optional) directory contains additional files related to the scan  

 Files from each acquisition step will be named according to acquisition step number inside a scan, so file name starts with `acqYYYY.` Example below is a run/scan (number 10) with 2 acquistion steps in it and with the request to output BS (.BSDATA.h5 files), EPICS(.PVDATA.h5 files) and two Jungfrau detectors (JF01T03V01 and JF03T01V02) for both of them - make a conversion from raw format, but keep raw files in addition (so raw_data/ directory is filled) and save results of dap pipeline:
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


<a id="bookkeeping"></a>
### Bookkeeping

 In case of successful (accepted by broker) request, complete parameters used for it will be saved in a `meta/` subdirectory of corresponding run/scan with name acqYYYY.json
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
 In addition we log in `logs/` directory the output of the retrieve actions by corresponding writers
```
$ pwd
/sf/cristallina/data/p21528/raw/run0001/logs
$ ls
acq0001.BSDATA.log      acq0004.JF16T03V01.log  acq0007.PVDATA.log      acq0011.BSDATA.log
acq0001.JF16T03V01.log  acq0004.PVDATA.log      acq0008.BSDATA.log      acq0011.JF16T03V01.log
acq0001.PVDATA.log      acq0005.BSDATA.log      acq0008.JF16T03V01.log  acq0011.PVDATA.log
acq0002.BSDATA.log      acq0005.JF16T03V01.log  acq0008.PVDATA.log      acq0012.BSDATA.log
acq0002.JF16T03V01.log  acq0005.PVDATA.log      acq0009.BSDATA.log      acq0012.JF16T03V01.log
acq0002.PVDATA.log      acq0006.BSDATA.log      acq0009.JF16T03V01.log  acq0012.PVDATA.log
acq0003.BSDATA.log      acq0006.JF16T03V01.log  acq0009.PVDATA.log      acq0013.BSDATA.log
acq0003.JF16T03V01.log  acq0006.PVDATA.log      acq0010.BSDATA.log      acq0013.JF16T03V01.log
acq0003.PVDATA.log      acq0007.BSDATA.log      acq0010.JF16T03V01.log  acq0013.PVDATA.log
acq0004.BSDATA.log      acq0007.JF16T03V01.log  acq0010.PVDATA.log

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

Example of log files above shows that there are missing pulseid's for some of the requested BS sources (SAROP31-PBPS149:YPOS), some BS sources are not available completely (SAR-CVME-TIFALL6:EvtSet); for Epics sources an information is displayed how many data points (N1) is retrieved and how do they distributed in respect to requested start/stop_pulseid interval - (N2[N3)N4), where N1=N2+N3+N4, N2/N4 are numbers of points before and after requested interval, N3 is within the pulseid interval. 

<a id="Example1"></a>
## Example1

 Command line example how to use broker to request a retireve of data is daq_client.py. To run is enough to have python > 3.6 and standard packages (requests, os, json)
(so standard PSI python environment is good for this purpose):
```bash
$ module load psi-python36/4.4.0 
$ python daq_client.py -h
usage: daq_client.py [-h] [-p PGROUP] [-d OUTPUT_DIRECTORY] [-c CHANNELS_FILE]
                     [-e EPICS_FILE] [-f FILE_DETECTORS]
                     [-r RATE_MULTIPLICATOR] [-s SCAN_STEP_FILE]
                     [--start_pulseid START_PULSEID]
                     [--stop_pulseid STOP_PULSEID]

test broker

optional arguments:
  -h, --help            show this help message and exit
  -p PGROUP, --pgroup PGROUP
                        pgroup, example p12345
  -d OUTPUT_DIRECTORY, --output_directory OUTPUT_DIRECTORY
                        output directory for the data, relative path to the
                        raw directory in the pgroup
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

<a id="Example2"></a>
## Example2

 Another example is more "start/stop" oriented way of doing data acquistion. To run this example one needs, in addition to daq_config.py, script client_example.py.
It can also run in a standard PSI environment, but the pulse_id's would be wrong (the proper way to get a pulse_id is to use one of the channel which provide them
effectively, see client_example.py). So in case one run this example in environment without pyepics, the guessed, fake pulseid would be approximately ok (due to the lock to the 50Hz electricity frequency for accelerator, our 100Hz is not an ideal 100Hz, so it's impossible to make a 100% accurate prediction from time to pulse_id)
```bash
. /opt/gfa/python 3.7 # this loads proper environment with pyepics in it
$ ipython
Python 3.7.5 (default, Oct 25 2019, 15:51:11)
Type 'copyright', 'credits' or 'license' for more information
IPython 7.2.0 -- An enhanced Interactive Python. Type '?' for help.

In [1]: import client_example as client                                                                                                                                   

In [2]: daq_client = client.BrokerClient(pgroup="p12345")                                                                                                                 

In [3]: daq_client.configure(output_directory="test/daq", channels_file="channel_list", rate_multiplicator=2, detectors_file="jf_jf01.json")                              

In [4]: daq_client.run(1000)                                                                                                                                              
[####################] 99% Run: 2
success: run number(request_id) is 2
```

 Note that you can "Ctrl-C" during "run" execution, with it you'll be asked do you want to "record" data which you took from start till pressing "Ctrl-C"
which is an illustration of the principle of the retrieve-based daq strategy - run(with RUN_NUMBER) will exist only when request to retrieve data is made.
Data are already recorded and present in buffers.

<a id="deployment"></a>
## Deployment

Current deployment of sf-daq_broker is done with [ansible](https://git.psi.ch/swissfel/sf-daq_install)

