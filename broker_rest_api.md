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

<a id="set_pvlist"></a>
## Update list of recorded by sf-daq EPICS channels

<a id="close_pgroup_writing"></a>
## Close permanently pgroup for writing by sf-daq

<a id="get_detector_settings"></a>
## Get detectors settings

<a id="set_detector_settings"></a>
## Set detector settings 

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
responce = r.json()
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
