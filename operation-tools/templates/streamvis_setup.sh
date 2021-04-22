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

envtest=$(conda env list | grep vis)

if [ $? != 0 ]; then
  echo "Creating the vis environment"
  conda config --append channels conda-forge
  conda config --append channels paulscherrerinstitute
  conda config --set channel_priority strict
  conda create -n vis -y streamvis={{ streamvis_version }}
fi
