#!/bin/bash

BZ_URL="http://bugtracker.kiwitcms.org/bugzilla/xmlrpc.cgi"
BZ_USER="admin@bugzilla.bugs"
BZ_PASS="password"

# this is Bug #1
bugzilla --bugzilla $BZ_URL --username $BZ_USER --password $BZ_PASS --ensure-logged-in \
    new --product TestProduct --version unspecified --component TestComponent \
    --summary 'Hello World' --comment 'This is reported via cli' \
    --os Linux  --arch All
