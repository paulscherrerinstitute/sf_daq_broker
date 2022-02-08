#!/bin/bash

rpm -qa | grep zeromq-devel | grep zeromq-devel-4.3. > /dev/null
if [ $? != 0 ]
then
    cd /etc/yum.repos.d/
    if [ ! -f network:messaging:zeromq:release-stable.repo ]
    then
        wget https://download.opensuse.org/repositories/network:messaging:zeromq:release-stable/RHEL_7/network:messaging:zeromq:release-stable.repo
    fi
    yum remove -y zeromq openpgm libsodium-devel
    yum install -y libsodium-devel zeromq-devel
fi

rpm -qa | grep zeromq-devel | grep zeromq-devel-4.3. > /dev/null
exit $?
