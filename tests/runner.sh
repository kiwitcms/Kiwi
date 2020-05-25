#!/bin/bash

# Note: execute this file from the project root directory

# setup
rm -rf /var/tmp/beakerlib-*/
export BEAKERLIB_JOURNAL=0

# install beakerlib from a fork b/c
# https://github.com/beakerlib/beakerlib/pull/11
if [ ! -f "/usr/share/beakerlib/beakerlib.sh" ]; then
    curl -o- https://raw.githubusercontent.com/atodorov/beakerlib/web-install/install.sh | bash
fi

# execute test scripts
./tests/test_docker.sh
./tests/test_http.sh
./tests/test_mysql_psql.sh


# look for failures
grep RESULT_STRING /var/tmp/beakerlib-*/TestResults | grep -v PASS && exit 1

# explicit return code for Makefile
exit 0
