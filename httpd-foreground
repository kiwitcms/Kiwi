#!/bin/bash

set -u

# Make sure we're not confused by old, incompletely-shutdown nginx
# context after restarting the container. Nginx won't start correctly
# if it thinks it is already running.
rm -rf /tmp/nginx* /tmp/kiwitcms*

# will execute in background so that uwsgi executes in
# the foreground and is able to log to stdout
/usr/sbin/nginx -e /dev/stderr -c /Kiwi/etc/nginx.conf

/venv/bin/uwsgi --ini /Kiwi/etc/uwsgi.conf
