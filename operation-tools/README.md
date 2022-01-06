# Configuration of sf-daq components via ansible

# Table of content
1. [Retrieval node](#retrieval)
2. [Receiver node](#receiver)
3. [Troubleshooting](#troubles)

<a id="retrieval"></a>
## Retrieval node

There are one production retrieval node and several development
| host  | Comment |
| ------------- | ------------- |
| broker_test  | Dev node  |
| broker_production  | Production node  |

 To install broker node:
```bash
ansible-playbook --extra-vars "host=broker_test" install_broker_node.yml
```

 To clean broker node from daq services installation:
 ```bash
 ansible-playbook --extra-vars "host=broker_test" clean_broker_node.yml
 ```

<a id="receiver"></a>
## Receiver node

For each beamline there is at least one main receiver node:
| host_id  | Comment |
| ------------- | ------------- |
| sf_daq_alvra  | Alvra  |
| sf_daq_bernina  | Bernina  |
| sf_daq_maloja | Maloja |

To cleanup receiver node from daq configuration:
  1. to cleanup just detector configuration, without cleaning up installed software
```bash
ansible-playbook --extra-vars "host={host_id}" clean_receiver_daq.config.yml
```
  2. to cleanup completely reciever node (detector configuration and software):
```bash
ansible-playbook --extra-vars "host={host_id}" clean_receiver_daq.all.yml
```
To install (after fresh daq installation or after cleanup) corresponding configuration:
```bash
ansible-playbook {configuration}.yml
e.g.
ansible-playbook daq4.JF06.yml
```
where {configuration} is from this table:
| configuration  | Comment |
| ------------- | ------------- |
| daq8.JF02_JF06-4M | Hamos+4M  |
| daq8.JF02_JF06  | Hamos+16M(unstable)  |
| daq8.JF06-4M_JF09_JF10 | Hamos + FLEX detectors |
| daq8.JF06-4M | 4M detector |
| daq8.JF06 | 16M detector |
| daq3.JF01_JF03_JF04_JF07 | 1p5M+I0+Fluo+16M |
| daq3.JF01_JF03_JF07-3m | 1p5M+I0+3modules_from16M |
| daq3.JF01_JF03_JF07_JF14 | 1p5M+I0+16M+RIXS |
| daq3.JF01_JF03_JF07 | 1p5M+I0+16M |
| daq3.JF01_JF03_JF13_JF14 | 1p5M+I0+Vacuum+RIXS |
| daq3.JF03_JF07_JF14 | I0+16M+RIXS |
| daq3.JF03_JF14 | I0+RIXS |
| daq3.JF14 | RIXS |
| daq9.JF15 | 1st Maloja Detector |

<a id="troubles"></a>
## Troubleshooting

### Problem with retrieval/broker node
Re-run broker node installation script 
```bash
ansible-playbook --extra-vars "host=broker_production" install_broker_node.yml
```
if problem persist, clean broker node from services and re-run installation:
```bash
ansible-playbook --extra-vars "host=broker_test" clean_broker_node.yml
ansible-playbook --extra-vars "host=broker_test" install_broker_node.yml
```

### Problem/reconfiguration of reciever node
In case reconfiguration of reciever node is needed (let's say Bernina switches to use combination 1p5M+I0, while before used configuration RIXS-only) - first clean previous detector configuration; then apply suitable configuration from blessed:
```bash
ansible-playbook --extra-vars "host=sf_daq_bernina" clean_receiver_daq.config.yml
ansible-playbook daq3.JF01_JF03_JF07.yml
```
