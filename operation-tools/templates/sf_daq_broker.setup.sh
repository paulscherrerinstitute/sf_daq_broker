#!/bin/bash

# needed, otherwise executing with Ansible won't work
# see: https://github.com/conda/conda/issues/7267
unset SUDO_UID SUDO_GID SUDO_USER

if [ ! -f /home/dbe/miniconda3/bin/conda ]
then
  echo "Getting Miniconda"
  wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
  sh Miniconda3-latest-Linux-x86_64.sh -b -p /home/dbe/miniconda3

  rm -rf Miniconda3-latest-Linux-x86_64.sh
fi

# Setup the conda environment.
source /home/dbe/miniconda3/etc/profile.d/conda.sh

CONDA_ENV_NAME=sf-daq
envtest=$(conda env list | grep ${CONDA_ENV_NAME})

if [ $? != 0 ]; then
  echo "Creating the ${CONDA_ENV_NAME} environment"
  conda create -y -n ${CONDA_ENV_NAME} -c paulscherrerinstitute -c conda-forge data_api jungfrau_utils bitshuffle=0.3.5

  conda deactivate
  conda activate ${CONDA_ENV_NAME}

  conda install -y -c conda-forge bottle pika ujson unidecode
  conda install -y -c slsdetectorgroup -c conda-forge slsdet=6.1.1
  conda install -y -c paulscherrerinstitute -c conda-forge pyepics
else
  conda deactivate
  conda activate ${CONDA_ENV_NAME}
fi

if [ ! -d /home/dbe/git ]; then
  echo "No git repo found, cloning it..."
  mkdir /home/dbe/git
fi

REPO=sf_daq_broker
if [ ! -d /home/dbe/git/${REPO} ]
then
  cd /home/dbe/git && git clone \
      https://github.com/paulscherrerinstitute/${REPO}.git

  echo "Setting up develop"
  cd /home/dbe/git/${REPO} && python setup.py develop

fi

