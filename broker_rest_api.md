# rest api of sf-daq broker

# Table of content
0. [General remarks](#general_remarks)
1. [/retrieve_from_buffers](#retrieve_from_buffers)
2. [/take_pedestal](#take_pedestal)
3. [/get_allowed_detector_list](#get_allowed_detector_list)
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

import json # for the pretty print of json output
responce = r.json()
print(json.dumps(responce, indent=4))
{
    "status": "ok"/"failed",
    "message": explanation_message_in_case_of_failure
}
```
In case of successful call (Status Code 200), return message contains `status` field with possible values : `ok` or `failed`. An explanation for the `failed` cases is given in the `message` field. Example of failed call (for the case when request is made without providing necessary information (`detector_name`) in the call):
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

<a id="get_allowed_detector_list"></a>
## Get list of allowed detectors for the beamline

<a id="get_running_detectors_list"></a>
## Get list of currently running detectors 

<a id="power_on_detector"></a>
## Power ON detector

<a id="get_next_run_number"></a>
## Get next acquisition run number

<a id="get_last_run_number"></a>
## Get last acquisition run number

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
