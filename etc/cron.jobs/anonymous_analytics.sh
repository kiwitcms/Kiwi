#!/bin/bash

# make sure Python is enabled
export VIRTUAL_ENV=/venv
export PATH=/venv/bin:${PATH}

# execute the actual Python script
cat /venv/lib64/python3.11/site-packages/tcms/cron/anonymous_analytics.py | /Kiwi/manage.py shell
