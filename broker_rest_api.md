# rest api of sf-daq broker

# Table of content
0. [General remarks](#general_remarks)
1. [/retrieve_from_buffers](#retrieve_from_buffers)
2. [/take_pedestal](#take_pedestal)
3. [/get_allowed_detectors_list](#get_allowed_detectors_list)
4. [/get_running_detectors_list](#get_running_detectors_list)
5. [/power_on_detector](#power_on_detector)
6. [/get_next_run_number](#get_next_run_number)
7. [/get_last_run_number](#get_last_run_number)
8. [/get_pvlist](#get_pvlist)
9. [/set_pvlist](#set_pvlist)
10. [/close_pgroup_writing](#close_pgroup_writing)
11. [/get_detector_settings](#get_detector_settings)
12. [/set_detector_settings](#set_detector_settings)
13. [/copy_user_files](#copy_user_files)
14. [/get_dap_settings](#get_dap_settings)
15. [/set_dap_settings](#set_dap_settings)

<a id="general_remarks"></a>
## General remarks
For the description of restAPI calls below and examples, the following variables needs to be set to a proper value (url's of broker instances). Example for the SwissFEL operation:
```
import requests
broker_address = "http://sf-daq:10002"
broker_slow_address = "http://sf-daq:10003"
```

In all examples code below, it is assumed that successful call to restAPI did happened. Example code to check this:
```
r = requests.get(f{broker_address}/{api_call}'
if r.status_code != 200:
    raise Exception(f'bad responce for daq {r.status_code} {r.text}')
# Got Status Code 0k (200), so can analyse reply from daq
```
for the pretty print of json output from the call, do not forget to import json module
```
import json # for the pretty print of json output
responce = r.json()
print(json.dumps(responce, indent=4))
{
    "status": "ok"/"failed",
    "message": explanation_message_in_case_of_failure
}
```
For almost all calls to broker described below (exceptions are : 
[/get_allowed_detectors_list](#get_allowed_detectors_list) and [/get_running_detectors_list](#get_running_detectors_list) ) - for the case of successful call (Status Code 200), return message contains `status` field with possible values : `ok` or `failed`. An explanation for the `failed` cases is given in the `message` field. Example of failed call (for the case when request is made without providing necessary information (`detector_name`) in the call):
```
print(json.dumps(r.json(), indent=4))
{
    "status": "failed",
    "message": "no detector name in the request"
}
```

<a id="retrieve_from_buffers"></a>
## Retrieve from buffers  

<a id="take_pedestal"></a>
## Take pedestal  
Use this call to take pedestal(dark) run for the detectors. Please check that the beam/laser are off during pedestal data taking, to be able to collect real dark data, without influences from the sources. Pedestal run should be taken at same conditions (pressure/temperature) as the data runs, for which this pedestal run will be applied. 

 It's possible and recommended to make one single pedestal run for several detectors, but include in the call only detectors which are "running" at that moment (list of running detector one can get with [/get_running_detectors_list](#get_running_detectors_list) call).

Example call for the pedestal run:
```
detectors = {"JF01T03V01": {}, "JF03T01V02": {} }
pgroup = "p17534"
rate_multiplicator = 1 # with which rate detectors are triggering at this moment (1-100Hz, 2-50Hz....). Default (if not provided - 1(100Hz))
r = requests.post(f'{broker_address}/take_pedestal', json={'pgroup': pgroup, 'detectors': detectors, 'rate_multiplicator': rate_multiplicator} )
```
Succesfull return of the call looks like this:
```
print(json.dumps(r.json(), indent=4))
{
    "status": "ok",
    "message": "will do a pedestal now, wait at least 40.0 seconds",
    "run_number": "0",
    "acquisition_number": "0",
    "unique_acquisition_number": "0"
}
```
While if there are problems with the call `(responce["status"] == "failed")`, check message field of the responce. Example for the case when detector not belonging/configured to the beamline is specified in the call:
```
print(json.dumps(r.json(), indent=4))
{
    "status": "failed",
    "message": "JF03T01V01 not belongs to the bernina"
}
```

<a id="get_allowed_detectors_list"></a>
## Get list of allowed detectors for the beamline
With this call one can get list of all the detectors which are configured for this beamline, as well as some detectors/daq parameters defined for that detectors. Example output for the Bernina beamline:
```
r = requests.get(f'{broker_address}/get_allowed_detectors_list' )
responce = r.json()
print(json.dumps(responce, indent=4))
{
    "detectors": [
        "JF01T03V01",
        "JF03T01V02",
        "JF04T01V01",
        "JF05T01V01",
        "JF07T32V02",
        "JF13T01V01",
        "JF14T01V01"
    ],
    "names": [
        "1p5M Bernina detector",
        "Bernina I0, 1 module",
        "Fluorescence, 1 module",
        "Stripsel, 1 module",
        "16M detector",
        "Vacuum detector",
        "RIXS detector"
    ],
    "visualisation_address": [
        "sf-daq-12:5001",
        "sf-daq-12:5003",
        "sf-daq-12:5004",
        "sf-daq-12:5005",
        "sf-daq-13:5007",
        "sf-daq-13:5013",
        "sf-daq-13:5014"
    ]
}
```
In the example above - 7 detectors `(responce.get('detectors', None))` are configured/known at the Bernina. Their "human names" are listed in the field `"names"` (so, for example, JF05T01V01 has name "Stripsel, 1 module") and `"visualisation_address"` contains location of [detector visualisation](https://github.com/paulscherrerinstitute/streamvis) (for JF05T01V01 visualisation runs on http://sf-daq-12:5005, as seen from example output above). 

<a id="get_running_detectors_list"></a>
## Get list of currently running detectors 
Result of this call will be a list of currently running detectors at the beamline. Example call (only one detector is running, JF03T01V02, as seen in this example):
```
r = requests.get(f'{broker_address}/get_running_detectors_list' )
responce = r.json()
print(json.dumps(responce, indent=4))
{
    "detectors": [
        "JF03T01V02"
    ]
}
running_detectors = responce.get("detectors", None)
```
Technically, this call runs through the list of [all configured detectors](/get_allowed_detectors_list) for the beamline and checks if there are fresh data available for the detector in the detector buffer (so in fact, this call checks the whole sequence that the detector is producing data and sf-daq writes that data to the detector buffer). In case of problems, check that detector is connected hardware wise (cooling, power, network, trigger...) and that [/power_on_detector](#power_on_detector) call is made already to apply HV to detector sensors and start detector triggering.

<a id="power_on_detector"></a>
## Power ON detector
This call is used to configure, apply HV to the sensors and start triggering of the detector. Before doing this call, make sure that detector is connected to cooling system, power, network and trigger (so hardware-wise detector is ready). Procedure may take up to few minutes (depending on number of modules in detector), so best is to wait sometime before trying to make another [power_on](#power_on_detector) request. To check if detector is running (so, procedure was succesfull) - use [/get_running_detectors_list](#get_running_detectors_list) call. 
```
detector_name = "JF03T01V02"
r = requests.post(f'{broker_address}/power_on_detector', json={'detector_name': detector_name} )
print(json.dumps(r.json(), indent=4))
{
    "status": "ok",
    "message": "request to power on detector is sent, wait few minutes"
}
```
Example output in case of failure in the call (here request is made to power on detector which doesn't belong to the beamline):
```
detector_name = "JF11T04V01"
r = requests.post(f'{broker_address}/power_on_detector', json={'detector_name': detector_name} )
print(json.dumps(r.json(), indent=4))
{
    "status": "failed",
    "message": "JF11T04V01 not belongs to the bernina"
}
```

<a id="get_next_run_number"></a>
## Get next acquisition run number
This call allows to generate a run number, which can be used in [/retrieve_from_buffers](#retrieve_from_buffers) request. The usual case of using this call is before the first acquisition step of the run to get such number and use it for all subsequent steps in that run(scan).

Example of call:
```
pgroup = "p17534"
r = requests.get(f'{broker_address}/get_next_run_number', json={'pgroup': pgroup} )
responce = r.json()
print(json.dumps(responce, indent=4))
{
    "status": "ok",
    "message": "22"
}
next_run_number = int(responce.get("message")) if responce["status"] == "ok" else None
```

Example of failed request to get next run number (pgroup is closed for writing, see [close_pgroup_writing](#close_pgroup_writing)):
```
print(json.dumps(r.json(), indent=4))
{
    "status": "failed",
    "message": "/sf/bernina/data/p19318/raw/ is closed for writing"
}
```

**Note**: each call to [/get_next_run_number](#get_next_run_number) generates a new number. If it's not used in corresponding [/retrieve_from_buffers](#retrieve_from_buffers) requests - that number are *lost*, there will be no data written for that run numbers.

Every call generates a new number:
```
for i in range(3):
    r = requests.get(f'{broker_address}/get_next_run_number', json={'pgroup': pgroup} )
    responce = r.json()
    next_run_number = int(responce.get("message")) if responce["status"] == "ok" else None
    print(f'call {i}: generated {next_run_number=}')

call 0: generated next_run_number=8
call 1: generated next_run_number=9
call 2: generated next_run_number=10
```
In case of need to know current run_number (so not generating/reserving a new one), use [/get_last_run_number](#get_last_run_number) call

<a id="get_last_run_number"></a>
## Get last acquisition run number
This call is to get a current run_number (illustrative case: to continue with the current run(scan) for the next acquisition steps):
```
pgroup = "p17534"
r = requests.get(f'{broker_address}/get_last_run_number', json={'pgroup': pgroup} )
responce = r.json()
print(json.dumps(responce, indent=4))
{
    "status": "ok",
    "message": "10"
}
last_run_number = int(responce.get("message")) if responce["status"] == "ok" else None
```
Comparing to [/get_next_run_number] - this call doesn't generate a new number each time, but returns a currently known to sf-daq (highest) run_number:
```
for i in range(3):
    r = requests.get(f'{broker_address}/get_last_run_number', json={'pgroup': pgroup} )
    responce = r.json()
    last_run_number = int(responce.get("message")) if responce["status"] == "ok" else None
    print(f'call {i}: generated {last_run_number=}')

call 0: generated last_run_number=10
call 1: generated last_run_number=10
call 2: generated last_run_number=10
```

<a id="get_pvlist"></a>
## Get list of recorded by sf-daq EPICS channels 
sf-daq runs separate CA channels (EPICS) buffer for each of the beamline. Only configured channels are recorded in the buffer and can be retrieved and be written to the data files. This call allows to get list of currently configured channels in the epics buffer.

Example of the call (two epics channels are monitored by epics buffer in this beamline):
```
r = requests.get(f'{broker_address}/get_pvlist')
print(json.dumps(r.json(), indent=4))
{
    "pv_list": [
        "ELCOMAT:X",
        "ELCOMAT:Y"
    ]
}
```
The only possible failure for the call can only be that there is no epics buffer configured/running for the beamline, in this case output will be:
```
print(json.dumps(r.json(), indent=4))
{
    "status": "failure, epics config file not exist for this beamline {beamline_name}"
}
```

<a id="set_pvlist"></a>
## Update list of recorded by sf-daq EPICS channels
With this call it's possible to setup/replace list of the monitored by epics buffer channels. To get current list of the channel, use [get_pvlist](#get_pvlist) call.

Example of the call:
```
pv_list = ["ELCOMAT:X", "ELCOMAT:Y", "SLAAR21-LSCP1-FNS:CH7:WFM"]
r = requests.post(f'{broker_address}/set_pvlist', json={'pv_list': pv_list})
print(json.dumps(r.json(), indent=4))
{
    "status": "ok",
    "message": [
        "ELCOMAT:X",
        "ELCOMAT:Y",
        "SLAAR21-LSCP1-FNS:CH7:WFM"
    ]
}
```
Please note that updating list of channel cause a restart of epics buffer for 10-40 seconds (so during that time, no recording to the buffer is happening). Do an update of epics setup only during pause in data taking.

<a id="close_pgroup_writing"></a>
## Close permanently pgroup for writing by sf-daq
To prevent accidental writing files to the wrong pgroup it's possible to *close pgroup* for further adding/writing files by sf-daq. Since this closing triggers also automatic archival of existing data, procedure is permanent (once pgroup is closed, it shouldn't be re-opened). In best practice, it's good to close pgroup when beamtime is over and it's known that there will be no new data collected with sf-daq. Preventing writing to pgroup affects only writing to ../raw/.. storage space of pgroup, so it's possible to add/modify files in ../res/.. or ../work/.. after closing. 

Example call to close pgroup for writing:
```
pgroup = "p17534"
r = requests.post(f'{broker_address}/close_pgroup_writing', json={'pgroup': pgroup} )
```
In case of success `(responce["status"] == "ok")`:
```
print(json.dumps(r.json(), indent=4))
{
    "status": "ok",
    "message": "p17534 closed for writing"
}
```

In case of failure(here a second attempt is made for already closed pgroup):
```
print(json.dumps(r.json(), indent=4))
{
    "status": "failed",
    "message": "/sf/bernina/data/p17534/raw/ is already closed for writing"
}
```

<a id="get_detector_settings"></a>
## Get detectors settings
Get detector settings (exposure time, delay, gain_mode ("dynamic", "fixed_gain1", "fixed_gain2"), gain settings("normal" or "low_noise")). 

Example of the call:
```
detector_name = "JF03T01V02"
r = requests.post(f'{broker_slow_address}/get_detector_settings', json={'detector_name': detector_name} )
```
In case of successful responce from broker `(responce["status"] == "ok")`:
```
print(json.dumps(r.json(), indent=4))
{
    "status": "ok",
    "exptime": 5e-06,
    "detector_mode": "normal",
    "delay": 0.00089,
    "gain_mode": "dynamic"
}
```
Example of the failed request (wrong name of detector):
```
detector_name = "JF03T01V01"
r = requests.post(f'{broker_slow_address}/get_detector_settings', json={'detector_name': detector_name} )
print(json.dumps(r.json(), indent=4))
{
    "status": "failed",
    "message": "JF03T01V01 not belongs to the bernina"
}
```

<a id="set_detector_settings"></a>
## Set detector settings 
Change detector parameter (**should be used with care and best to consult responsible for daq and detector people first. Highly experimental feature at the moment**). Detector parameters obtained with [get_detector_settings](#get_detector_settings) can be changed with this call.

Example how to change detector delay (which may cause mis-sinchronisation with the xfel pulse):
```
detector_name = "JF03T01V02"
r = requests.post(f'{broker_slow_address}/set_detector_settings', json={'detector_name': detector_name, "delay": 0.00088} )
```
Check in responce that operation was made by the broker:
```
print(json.dumps(r.json(), indent=4))
{
    "status": "ok"
}
```
but in addition, cross check with [get_detector_settings](#get_detector_settings) that changes did really happened:
```
r = requests.post(f'{broker_slow_address}/get_detector_settings', json={'detector_name': detector_name} )
print(json.dumps(r.json(), indent=4))
{
    "status": "ok",
    "exptime": 5e-06,
    "detector_mode": "normal",
    "delay": 0.00088,
    "gain_mode": "dynamic"
}
```
In case broker can't make an operation, `failed` status will be returned with the message explaining the failure(in this example, problem with the timing system occured, preventing to stop detector to change settings):
```
print(json.dumps(r.json(), indent=4))
{
    "status": "failed",
    "message": "tried to stop detector trigger but failed"
}
```

<a id="copy_user_files"></a>
## Saving files using sf-daq  
With this call it's possible to save user files together with the files produced by sf-daq. Users files will be saved in `raw/runXXXX/aux` directory (for details see [directory structure](https://github.com/paulscherrerinstitute/sf_daq_broker#directory-structure)). Source of the files should be storage place accessible by the broker (pgroup `/res/` directory is a perfect example of such place, while home directory of gac- account is an example of unaccessible directory by broker)

Example of the call:
```
pgroup = 'p17502'
run_number = 13
files_list = ['/sf/alvra/data/p17502/res/test/test1.json', '/sf/alvra/data/p17502/res/test/test2.json', '/sf/alvra/data/p17502/res/test/test3.json']
r = requests.post(f'http://{broker_slow_address}/copy_user_files', json={'pgroup': pgroup, 'run_number': run_number, 'files': files_list })
```

In case of successful call to broker (`responce["status"] == "ok"`) responce will contain information with the full destination path of copied files as well as list of files which are not copied (not accessible by the broker). Example below illustrate case where test1/2.json files exists, while test3.json - not, so can't be copied by the broker:
```
print(json.dumps(r.json(), indent=4))
{
    "status": "ok",
    "message": "user file copy finished, check error_files list",
    "error_files": [
        "/sf/alvra/data/p17502/res/test/test3.json"
    ],
    "destination_file_path": [
        "/sf/alvra/data/p17502/raw/run0013/aux/test1.json",
        "/sf/alvra/data/p17502/raw/run0013/aux/test2.json"
    ]
}
```
**Note** : in case files with same name already exists in `/aux/` directory - they will be overwritten. If same filename (from different source directories) is specified(e.g. ../res/test1/test.json and ../res/test2/test.json) - only last one will be copied successfully and in this case `error_files` will not contain other files (they were copied successfuly, but were overwritten afterwards)

Example of failed request (here case, where yet no run with number 80 taken):
```
print(json.dumps(r.json(), indent=4))
{
    "status": "failed",
    "message": "no such run 80 in the pgroup"
}
```
<a id="get_dap_settings"></a>
## get current DAP settings for detector
Retrieve current dap parameters for the specified detector. For the descrtiption of dap parameters, see [dap](https://gitlab.psi.ch/sf-daq/dap)

Example of the call:
```
detector_name = "JF06T08V04"
r = requests.post(f'{broker_slow_address}/get_dap_settings', json={'detector_name': detector_name} )
```
Example of succesfull (`responce["status"] == "ok"`) return of dap parameters:
```
print(json.dumps(r.json(), indent=4))
{
    "status": "ok",
    "message": {
        "beam_center_x": 1119.0,
        "beam_center_y": 1068.0,
        "detector_distance": 0.092,
        ...<skipped>...
    }
}
```
In case of the failure `(responce["status"] == "failed")`, check corresponding message in the responce body. Example below illustrate case where dap pipeline is (probably) not enabled for the particular detector:
```
detector_name = "JF11T04V01"
r = requests.post(f'{broker_slow_address}/get_dap_settings', json={'detector_name': detector_name} )
print(json.dumps(r.json(), indent=4))
{
    "status": "failed",
    "message": "dap parameters file is not existing, contact support"
}

```

<a id="set_dap_settings"></a>
## set DAP settings for detector
Use to change dap parameters for the particular detector. Current list of dap parameters can be retrieved with [get_dap_settings](#get_dap_settings). For complete list of dap parameters amd implemented algorithms, see [dap](https://gitlab.psi.ch/sf-daq/dap)

Example of the call:
```
parameters = {}
detector_name = "JF06T08V04"
parameters = {"detector_distance": 0.091}
r = requests.post(f'{broker_slow_address}/set_dap_settings', json={'detector_name': detector_name, 'parameters': parameters})
responce = r.json()
```
On success `(responce["status"] == "ok")` `message` contains values of the changed parameters (in example below, `detector_distance` was changed from 0.092 to 0.091):
```
print(json.dumps(responce, indent=4))
{
    "status": "ok",
    "message": {
        "detector_distance": [
            0.092,
            0.091
        ]
    }
}

```
Example (in this example request is made for none existing detector) of the failure `(responce["status"] == "failed")`:
```
print(json.dumps(r.json(), indent=4))
{
    "status": "failed",
    "message": "JF06T08V03 not belongs to the alvra"
}
```
