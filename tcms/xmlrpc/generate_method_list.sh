#!/bin/bash

awk '/^def/ { gsub(/\(/, " "); print "\x27"$2"\x27,"}' $@

