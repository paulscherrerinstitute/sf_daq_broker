# REST API of sf-daq_broker

# Table of content
1. [General remarks](#general_remarks)
2. [/retrieve_from_buffers](#retrieve_from_buffers)
3. [/take_pedestal](#take_pedestal)
4. [/get_allowed_detectors_list](#get_allowed_detectors_list)
5. [/get_running_detectors_list](#get_running_detectors_list)
6. [/power_on_detector](#power_on_detector)
7. [/get_next_run_number](#get_next_run_number)
8. [/get_last_run_number](#get_last_run_number)
9. [/get_pvlist](#get_pvlist)
10. [/set_pvlist](#set_pvlist)
11. [/close_pgroup_writing](#close_pgroup_writing)
12. [/get_detector_settings](#get_detector_settings)
13. [/set_detector_settings](#set_detector_settings)
14. [/copy_user_files](#copy_user_files)
15. [/get_dap_settings](#get_dap_settings)
16. [/set_dap_settings](#set_dap_settings)

<a id="general_remarks"></a>
## General remarks

Before using the REST API calls for **sf-daq_broker**, it's essential to set up the necessary variables and handle responses appropriately. Here's a guide to working with these API calls:

### Setting Up Variables

Firstly, initialize the required variables, such as `broker_address` and `broker_slow_address`, pointing to the appropriate URLs where the sf_daq_broker instances are hosted. Here's an example of setting these variables for a SwissFEL operation:
```python
import requests

# Replace these addresses with the actual URLs of the broker instances
broker_address = "http://sf-daq:10002"
broker_slow_address = "http://sf-daq:10003"
```

### Handling API Responses

When making requests to the broker, it's crucial to handle responses appropriately. Always check the response status code and content for successful execution or possible errors. Here's an example:
```python
import json

# Example API call to retrieve data
api_call = "/get_allowed_detectors_list"
r = requests.get(f"{broker_address}{api_call}")

# Check if the request was successful (Status Code 200)
if r.status_code == 200:
    # Analyze the response from the broker
    response = r.json()
    print(json.dumps(response, indent=4))
    """
    Example successful response:
    {
        "detectors": [
            "JF01T03V01",
            "JF03T01V02",
        # Additional response data...
    }
    """
else:
    # Handle failed request
    raise Exception(f"Bad response from daq: {r.status_code} {r.text}")
```

### Additional Notes


* **Pretty-Printing JSON Output**: The `json.dumps()` function helps format the JSON response for easier readability.
* **Error Handling**: For almost all calls, successful responses have a `status` field indicating `ok`, while failures contain a `status` field with explanations in the `message` field.
* **Exception Handling**: Always ensure to handle exceptions appropriately to avoid unexpected behavior in your application.

By following these guidelines, you can effectively interact with the sf_daq_broker REST API and handle responses in a structured manner.

<a id="retrieve_from_buffers"></a>
## Retrieve Data from Buffers

Use this API call to retrieve data from the buffers maintained by the SF-DAQ system. The call requires specific parameters for a successful data retrieval process.

### Example Call

```python
import requests

broker_address = "http://sf-daq:10002"
TIMEOUT_DAQ = 10

# Define mandatory parameters
parameters = {
    "pgroup": "p12345",
    "start_pulseid": 1000,
    "stop_pulseid": 2000,
    "pv_list": ["ELCOMAT:X", "ELCOMAT:Y"]
}

# Make the API call to retrieve data
r = requests.post(f'{broker_address}/retrieve_from_buffers', json=parameters, timeout=TIMEOUT_DAQ)

# Handle the response
if r.status_code == 200:
    response = r.json()
    print(response)
    """
    Successful Response:
    {
        "status": "ok",
        "message": "OK",
        "run_number": "10",
        "acquisition_number": "1",
        "unique_acquisition_number": "101",
        "files": ["/sf/alvra/data/p17502/raw/run0010/data/acq0001.PVDATA.h5"]
    }
    """
else:
    raise Exception(f"Bad response for retrieve_from_buffers: {r.status_code} {r.text}")
```

### Handling Response

* Successful Response: The call returns a status of 'ok' along with additional details like the run number, acquisition number, unique acquisition number, and a list of files produced by SF-DAQ for the retrieved data.
* Failed Response: In case of issues with the request or internal problems within SF-DAQ, the call returns a status of 'failed' along with an error description.

### Parameters

The 'parameters' passed in the request are a dictionary. Mandatory key-value pairs that need to be present include:

* `"pgroup"`: The group identifier for the data to retrieve.
* `"start_pulseid"`: The starting pulse ID for the data retrieval.
* `"stop_pulseid"`: The stopping pulse ID for the data retrieval.

Failure to provide any of these mandatory parameters will result in the broker declining the data retrieval request.

Optional Parameters

Additionally, there are several optional parameters that can be included:

* `"run_number"`: Integer indicating the current acquisition as part of a scan. If not provided, a new run number is generated and returned.
* `"append_user_tag_to_data_dir"`: Boolean flag to append a "user_tag" to the run directory name. Defaults to False.
* `"user_tag"`: String with user-defined characters to append to the run directory name.
* `"rate_multiplicator"`: Integer indicating the beam rate expectation. Default is 1 (corresponds to 100Hz).
* `"channels_list"`: List of source names from the DataBuffer.
* `"camera_list"`: List of camera names.
* `"pv_list"`: List of EPICS PV names to retrieve from the epics buffer.
* `"detectors"`: Dictionary containing detector names and their respective parameters.
* `"scan_info"`: Dictionary specifying that this request belongs to a particular scan.

Any other fields/values included in the parameters dictionary will be ignored by the broker but saved in the metadata file. This allows for propagation of useful parameters for use in post-processing.

Detector Parameters

When providing detector-specific parameters within the "detectors" key:

* `"disabled_modules"` (list(int)): List of modules to disable for the detector.
* `"save_dap_results"` (bool): Save results from DAP processing.
* `"selected_pulse_ids"` (list(int)): Output only pulse IDs present in the list within the specified by start_/stop_pulseid region.
* `"save_ppicker_events_only"` (bool): Output only detector frames with pulse picker open within the specified pulse IDs region.
* `"compression"` (bool): Apply bitshuffle+lz4 compression.
* `"adc_to_energy"` (bool): Apply gain and pedestal corrections, converting raw detector values into energy.

    Additional parameters apply only when `adc_to_energy` is **True**.

    * `"mask"` (bool): Perform masking of bad pixels (assign them to 0).

    * `"double_pixels_action"` (str): Handling of double pixels at chip inner edges.

    * `"geometry"` (bool): Apply geometry correction.

    * `"gap_pixels"` (bool): Add gap pixels between detector chips.

    * `"factor"` (float, None): Divide all pixel values by a factor and round the result.

    * `"roi"` (tuple or dictionary): Regions of interest to output from the detector image.

    * `"downsample"` (tuple(int N, int M)): Reduce image using NxM pixels block.

<a id="take_pedestal"></a>
## Take pedestal  

Use this call to initiate a pedestal (dark) run for detectors. This step is crucial for collecting unbiased dark data, ensuring accurate subsequent measurements.

### Guidelines for Pedestal Run

Ensure the following during pedestal data collection:

* *Beam/Laser Off*: Collect genuine dark data by turning off the beam or laser.
* *Matching Conditions*: Maintain similar conditions (pressure/temperature) as data runs where the pedestal will be applied.

## Example Pedestal Run

```python
import requests
import json

# Define pedestal run parameters
detectors = {"JF01T03V01": {}, "JF03T01V02": {}}
pgroup = "p17534"
rate_multiplicator = 1
pedestal_request = {
    'pgroup': pgroup,
    'detectors': detectors,
    'rate_multiplicator': rate_multiplicator
}

# Initiate pedestal run
pedestal_url = f"{broker_address}/take_pedestal"
r = requests.post(pedestal_url, json=pedestal_request)

# Handle response
if r.status_code == 200:
    response = r.json()
    print(json.dumps(response, indent=4))
    """
    Example successful response:
    {
        "status": "ok",
        "message": "will do a pedestal now, wait at least 40.0 seconds",
        "run_number": "0",
        "acquisition_number": "0",
        "unique_acquisition_number": "0"
    }
    """
    """
    Example of failure:
    {
        "status": "failed",
        "message": "JF03T01V01 not belongs to the bernina"
    }
    """
}
else:
    raise Exception(f"Bad response for daq: {r.status_code} {r.text}")
```

### Handling Response

* Successful responses confirm the initiation of the pedestal run, providing run and acquisition details.
* Failed responses contain explanations in the message field, such as incorrect detector configuration.

## Note

Ensure detectors specified for the pedestal run belong to the respective beamline and are appropriately configured.

<a id="get_allowed_detectors_list"></a>
## Get Allowed Detectors List

Retrieve the list of detectors configured for the beamline along with their specific details.

## Example Call

```python
import requests 
import json

# Make the API call to get allowed detectors list
allowed_detectors_url = f"{broker_address}/get_allowed_detectors_list"
r = requests.get(allowed_detectors_url)

# Check for a successful response and handle accordingly
if r.status_code == 200:
    response = r.json()
    print(json.dumps(response, indent=4))
    """
    Example response:
    {
        "detectors": [
            "JF01T03V01",
            "JF03T01V02",
            ...
        ],
        "names": [
            "1p5M Bernina detector",
            "Bernina I0, 1 module",
            ...
        ],
        "visualisation_address": [
            "sf-daq-12:5001",
            "sf-daq-12:5003",
            ...
        ]
    }
    """
else:
    raise Exception(f"Bad response for daq: {r.status_code} {r.text}")
```

### Handling Response

* Successful responses contain a list of detectors configured for the beamline, their human-readable names, and visualisation addresses.
* Failed responses might occur if there's an issue with the request or if detectors aren't properly configured.

<a id="get_running_detectors_list"></a>
## Get Running Detectors List

Retrieve the list of detectors currently recording data to the DetectorBuffer.

### Example Call
```python
import requests
import json

# Make the API call to get the list of running detectors
running_detectors_url = f"{broker_address}/get_running_detectors_list"
r = requests.get(running_detectors_url)

# Check for a successful response and handle accordingly
if r.status_code == 200:
    response = r.json()
    print(json.dumps(response, indent=4))
    """
    Example response:
    {
        "detectors": [
            "JF03T01V02"
        ]
    }
    """
else:
    raise Exception(f"Bad response for daq: {r.status_code} {r.text}")
```
Handling Response

* Successful responses provide a list of detectors currently running at the beamline.

<a id="power_on_detector"></a>
## Power ON detector

Activate and configure a specific detector by applying necessary settings such as HV to sensors and triggering.

### Example Call

```python
import requests
import json

# Define the detector to power on
detector_name = "JF03T01V02"

# Make the API call to power on the detector
power_on_url = f"{broker_address}/power_on_detector"
power_on_request = {'detector_name': detector_name}
r = requests.post(power_on_url, json=power_on_request)

# Check for a successful response and handle accordingly
if r.status_code == 200:
    response = r.json()
    print(json.dumps(response, indent=4))
    """
    Example response:
    {
        "status": "ok",
        "message": "Request to power on detector sent. Wait a few minutes."
    }
    """
    """
    Example in case of failure:
    {
        "status": "failed",
        "message": "JF03T01V02 not belongs to the furka"
    }
    """
else:
    raise Exception(f"Bad response for daq: {r.status_code} {r.text}")
```

### Handling Response

* Successful responses confirm the request to power on the detector, providing a confirmation message.
* Failed responses might occur due to incorrect detector naming or if the detector doesn't belong to the specified beamline.

### Note

Ensure the detector specified for powering on is properly configured and connected to necessary hardware elements such as cooling, power, network, and trigger systems before making this call.

<a id="get_next_run_number"></a>
## Get Next Acquisition Run Number

Generate a run number for the next data acquisition process to ensure sequential data organization.

### Example Call

```python
import requests
import json

# Define the processing group
pgroup = "p17534"

# Make the API call to get the next run number
next_run_number_url = f"{broker_address}/get_next_run_number"
next_run_number_request = {'pgroup': pgroup}
r = requests.get(next_run_number_url, json=next_run_number_request)

# Check for a successful response and handle accordingly
if r.status_code == 200:
    response = r.json()
    print(json.dumps(response, indent=4))
    """
    Example response:
    {
        "status": "ok",
        "message": "22"
    }
    """
    """
    Example of failure:
    {
        "status": "failed",
        "message": "/sf/alvra/data/p17534/raw/ is closed for writing"
    }
    """
    next_run_number = int(response.get("message")) if response["status"] == "ok" else None
else:
    raise Exception(f"Bad response for daq: {r.status_code} {r.text}")
```

### Handling Response

* Successful responses provide the generated next run number for data acquisition.
* Failed responses might occur if the processing group is closed for writing or if there's an issue with acquiring the next run number.

### Note

Ensure the call for the next run number is made in a sequential manner to maintain data organization and prevent loss of acquired data due to non-usage of generated run numbers.

<a id="get_last_run_number"></a>
## Get Last Acquisition Run Number

Retrieve the most recently generated run number for data acquisition in a pgroup.

### Example Call

```python
import requests
import json

# Define the processing group
pgroup = "p17534"

# Make the API call to get the last run number
last_run_number_url = f"{broker_address}/get_last_run_number"
last_run_number_request = {'pgroup': pgroup}
r = requests.get(last_run_number_url, json=last_run_number_request)

# Check for a successful response and handle accordingly
if r.status_code == 200:
    response = r.json()
    print(json.dumps(response, indent=4))
    """
    Example response:
    {
        "status": "ok",
        "message": "10"
    }
    """
    last_run_number = int(response.get("message")) if response["status"] == "ok" else None
else:
    raise Exception(f"Bad response for daq: {r.status_code} {r.text}")
```

### Handling Response

* Successful responses provide the most recent run number generated for data acquisition within the processing group.
* Failed responses might occur if there are issues with retrieving the last run number, such as the processing group being closed for writing or other errors.

### Note

This call returns the last generated run number for data acquisition for the specified pgroup. In cases where multiple simultaneous scans or runs are ongoing, using this number might lead to confusion. 

<a id="get_pvlist"></a>
## Get List of Recorded EPICS Channels

Retrieve the list of EPICS (CA) channels currently recorded by the **sf-daq** for a specific beamline.

### Example Call

```python
import requests
import json

# Make the API call to retrieve the list of EPICS channels
epics_channels_url = f"{broker_address}/get_pvlist"
r = requests.get(epics_channels_url)

# Check for a successful response and handle accordingly
if r.status_code == 200:
    response = r.json()
    print(json.dumps(response, indent=4))
    """
    Example response:
    {
        "pv_list": [
            "ELCOMAT:X",
            "ELCOMAT:Y"
        ]
    }
    """
    """
    Example in case of failure:
    {
        "status": "failure, epics config file not exist for this beamline {beamline_name}"
    }
    """
    epics_channels = response.get("pv_list", [])
else:
    raise Exception(f"Bad response for daq: {r.status_code} {r.text}")
```

### Handling Response

* Successful responses provide a list of currently configured EPICS channels for the specified beamline.
* Failed responses occur if there's no configuration or setup for EPICS buffer for the specified beamline.

<a id="set_pvlist"></a>
## Update List of Recorded EPICS Channels

Update or set up the list of EPICS channels to be recorded by the sf_daq for a specific beamline.

### Example Call
```python
import requests
import json

# Define the list of EPICS channels to update or set
new_epics_channels = ["ELCOMAT:X", "ELCOMAT:Y", "SLAAR21-LSCP1-FNS:CH7:WFM"]

# Make the API call to update or set EPICS channels
update_epics_channels_url = f"{broker_address}/set_pvlist"
update_epics_request = {'pv_list': new_epics_channels}
r = requests.post(update_epics_channels_url, json=update_epics_request)

# Check for a successful response and handle accordingly
if r.status_code == 200:
    response = r.json()
    print(json.dumps(response, indent=4))
    """
    Example response:
    {
        "status": "ok",
        "message": [
            "ELCOMAT:X",
            "ELCOMAT:Y",
            "SLAAR21-LSCP1-FNS:CH7:WFM"
        ]
    }
    """
else:
    raise Exception(f"Bad response for daq: {r.status_code} {r.text}")
```

### Handling Response

* Successful responses confirm the update or setup of EPICS channels for recording by sf_daq.
* Failed responses might occur due to issues in the provided EPICS channels list or configurations.

### Note

Updating or setting EPICS channels triggers a restart of the EPICS buffer. During this restart, there will be a brief interruption in recording to the buffer. It's advisable to perform updates during pauses in data acquisition to avoid disruption to ongoing recording processes.

<a id="close_pgroup_writing"></a>
## Close Pgroup Writing

Close the designated pgroup for further writing by the sf_daq, preventing accidental file writing to the wrong pgroup.

### Example Call

```python
import requests
import json

# Define the pgroup to close for writing
pgroup_to_close = "p17534"

# Make the API call to close the specified pgroup
close_pgroup_url = f"{broker_address}/close_pgroup_writing"
close_pgroup_request = {'pgroup': pgroup_to_close}
r = requests.post(close_pgroup_url, json=close_pgroup_request)

# Check for a successful response and handle accordingly
if r.status_code == 200:
    response = r.json()
    print(json.dumps(response, indent=4))
    """
    Example response:
    {
        "status": "ok",
        "message": "p17534 closed for writing"
    }
    """
    """
    Example of failure:
    {
        "status": "failed",
        "message": "/sf/bernina/data/p17534/raw/ is already closed for writing"
    }
    """
else:
    raise Exception(f"Bad response for daq: {r.status_code} {r.text}")
```

### Handling Response

* Successful responses confirm the closure of the specified pgroup for writing by the sf_daq.
* Failed responses might occur if the pgroup is already closed for writing or due to other issues.

### Note

Closing a pgroup for writing by the sf_daq affects only the writing of files to the ../raw/.. storage space within the specified pgroup. Other directories like ../res/.. or ../work/.. remain unaffected, allowing additional file modifications even after the closure.

Additionally, upon closing a pgroup, an automatic archival process is initiated for the existing data within that pgroup. 

Closing a pgroup for writing is recommended practice, especially when a specific data collection phase is completed or when no further data acquisition is anticipated with the sf_daq. Be mindful that the closure is irreversible and is intended to prevent unintended data writing to the raw/ storage space, ensuring data integrity and organization.

<a id="get_detector_settings"></a>
## Get Detector Settings

Retrieve the current settings of a specific detector, including exposure time, delay, and gain mode.

### Example Call

```python
import requests
import json

# Define the detector name to retrieve settings
detector_name = "JF03T01V02"

# Make the API call to retrieve detector settings
get_settings_url = f"{broker_slow_address}/get_detector_settings"
get_settings_request = {'detector_name': detector_name}
r = requests.post(get_settings_url, json=get_settings_request)

# Check for a successful response and handle accordingly
if r.status_code == 200:
    response = r.json()
    print(json.dumps(response, indent=4))
    """
    Example response:
    {
        "status": "ok",
        "exptime": 5e-06,
        "detector_mode": "normal",
        "delay": 0.00089,
        "gain_mode": "dynamic"
    }
    """
else:
    raise Exception(f"Bad response for daq: {r.status_code} {r.text}")
```

### Handling Response

* Successful responses provide the current settings for the specified detector.
* Failed responses might occur due to issues with the provided detector name or other configuration problems.

### Detector Settings Example

Here's an example of potential detector settings:

```json
{
    "exposure_time": 0.000005, // Exposure time in seconds (5 microseconds)
    "detector_mode": "normal", // Detector mode: 'normal', 'low_noise'
    "delay": 0.00089, // Delay in seconds
    "gain_mode": "dynamic" // Gain mode: 'dynamic', 'fixed_gain1', 'fixed_gain2'
}
```
These settings represent typical configurations for a detector. The values might vary based on the specific detector model, beamline requirements, or experimental setup. Adjustments to these parameters can significantly impact data acquisition and quality.

<a id="set_detector_settings"></a>
## Set Detector Settings

Modify specific parameters of a detector's settings. **Caution**: altering settings without proper understanding or consultation with responsible personnel might disrupt data acquisition or lead to undesirable results. This feature is highly experimental and should be used with extreme care.

### Example Call

```python
import requests
import json

# Define the detector name and parameters to modify
detector_name = "JF03T01V02"
parameters_to_change = {"delay": 0.00088}

# Make the API call to set detector settings
set_settings_url = f"{broker_slow_address}/set_detector_settings"
set_settings_request = {'detector_name': detector_name, 'parameters': parameters_to_change}
r = requests.post(set_settings_url, json=set_settings_request)

# Check for a successful response and handle accordingly
if r.status_code == 200:
    response = r.json()
    print(json.dumps(response, indent=4))
    """
    Example response:
    {
        "status": "ok"
    }
    """
else:
    raise Exception(f"Bad response for daq: {r.status_code} {r.text}")
```

### Handling Response

* Successful responses confirm the modification of detector settings.
* Failed responses might occur due to issues with the provided detector name, parameters, or other configuration constraints.

<a id="copy_user_files"></a>
## Copy User Files

This call enables users to save additional files alongside those produced by sf-daq. The user files will be stored in the `raw/runXXXX/aux` directory (refer to [directory structure](https://github.com/paulscherrerinstitute/sf_daq_broker#directory-structure)) for details. The source of these files should be from a storage location accessible by the broker, such as the pgroup's /res/ directory.

### Example Call

```python
import requests
import json

# Define the pgroup, run number, and files to copy
pgroup = 'p17502'
run_number = 13
files_list = [
    '/sf/alvra/data/p17502/res/test/test1.json',
    '/sf/alvra/data/p17502/res/test/test2.json',
    '/sf/alvra/data/p17502/res/test/test3.json'
]

# Make the API call to copy user files
copy_files_url = f'http://{broker_slow_address}/copy_user_files'
copy_files_request = {'pgroup': pgroup, 'run_number': run_number, 'files': files_list}
r = requests.post(copy_files_url, json=copy_files_request)

# Check for a successful response and handle accordingly
if r.status_code == 200:
    response = r.json()
    print(json.dumps(response, indent=4))
    """
    Example response:
    {
        "status": "ok",
        "message": "User file copy finished, check error_files list",
        "error_files": [
            "/sf/alvra/data/p17502/res/test/test3.json"
        ],
        "destination_file_path": [
            "/sf/alvra/data/p17502/raw/run0013/aux/test1.json",
            "/sf/alvra/data/p17502/raw/run0013/aux/test2.json"
        ]
    }
    """
    """
    Example response of the failure:
    {
        "status": "failed",
        "message": "no such run 80 in the pgroup"
    }
    """
else:
    raise Exception(f"Bad response for daq: {r.status_code} {r.text}")
```

### Handling Response

* Successful responses indicate the completion of the user file copy process, providing details of copied files and list of files which was not possible to process.
* Failed responses might occur if the specified run doesn't exist in the provided pgroup or due to other issues.

### Note

In cases where files with the same names already exist in the /aux/ directory, they will be overwritten. It's essential to ensure the correctness of file paths and avoid unintended overwrites of important data.

<a id="get_dap_settings"></a>
## Get DAP Settings for Detector

Retrieve the current DAP (Data Analysis Pipeline) parameters for a specified detector. For a comprehensive understanding of DAP parameters, refer to [dap](https://gitlab.psi.ch/sf-daq/dap).

### Example Call

```python
import requests
import json

# Define the detector name
detector_name = "JF06T08V04"

# Make the API call to retrieve DAP settings
dap_settings_url = f'{broker_slow_address}/get_dap_settings'
dap_settings_request = {'detector_name': detector_name}
r = requests.post(dap_settings_url, json=dap_settings_request)

# Check for a successful response and handle accordingly
if r.status_code == 200:
    response = r.json()
    print(json.dumps(response, indent=4))
    """
    Example response:
    {
        "status": "ok",
        "message": {
            "beam_center_x": 1119.0,
            "beam_center_y": 1068.0,
            "detector_distance": 0.092,
            ...
        }
    }
    """
    """
    Example of response of the failure:
    {
        "status": "failed",
        "message": "dap parameters file is not existing, contact support"
    }
    """
else:
    raise Exception(f"Bad response for daq: {r.status_code} {r.text}")
```

### Handling Response

* Successful responses provide the current DAP parameters for the specified detector.
* Failed responses might occur if DAP settings for the specified detector are not available.

<a id="set_dap_settings"></a>
## Set DAP Settings for Detector

Use this call to modify DAP parameters for a particular detector. Ensure a clear understanding of the implications before making changes.

### Example Call
```python
import requests
import json

# Define the detector name and the parameters to change
detector_name = "JF06T08V04"
parameters = {"detector_distance": 0.091}  # Example: modifying detector_distance

# Make the API call to set DAP settings
set_dap_settings_url = f'{broker_slow_address}/set_dap_settings'
set_dap_settings_request = {'detector_name': detector_name, 'parameters': parameters}
r = requests.post(set_dap_settings_url, json=set_dap_settings_request)

# Check for a successful response and handle accordingly
if r.status_code == 200:
    response = r.json()
    print(json.dumps(response, indent=4))
    """
    Example response:
    {
        "status": "ok",
        "message": {
            "detector_distance": [
                0.092,
                0.091
            ]
        }
    }
    """
else:
    raise Exception(f"Bad response for daq: {r.status_code} {r.text}")
```

### Handling Response

* Successful responses indicate that the DAP parameters for the specified detector have been successfully modified.
* Failed responses might occur due to issues with the specified detector or incorrect parameter values.
