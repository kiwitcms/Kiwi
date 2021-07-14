#!/bin/bash

# Note: execute this file from the project root directory

# setup
rm -rf /var/tmp/beakerlib-*/
export BEAKERLIB_JOURNAL=0

# install beakerlib from source b/c beakerlib doesn't ship
# .deb packages
if [ ! -f "/usr/share/beakerlib/beakerlib.sh" ]; then
    sudo apt-get update
    sudo apt-get install git make
    git clone https://github.com/beakerlib/beakerlib.git
    make -C beakerlib/ install
fi

# execute test scripts
./tests/test_docker.sh
./tests/test_http.sh


# look for failures
cat /var/tmp/beakerlib-*/TestResults || exit 11
grep RESULT_STRING /var/tmp/beakerlib-*/TestResults | grep -v PASS && exit 22

# explicit return code for Makefile
exit 0
