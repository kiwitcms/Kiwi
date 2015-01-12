# -*- coding: utf-8 -*-
from django import dispatch

# Define the signals built-in TCMS internal
initial = dispatch.Signal()
create = dispatch.Signal()
update = dispatch.Signal()
delete = dispatch.Signal()
clean = dispatch.Signal()
