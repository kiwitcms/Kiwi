# -*- coding: utf-8 -*-
import re


def timedelta2int(value):
    """convert string nh(ay):nh(our):nm(inute) to integer seconds."""
    value = value.replace(' ', '')
    second_regex = re.compile(r'\d+s')
    minute_regex = re.compile(r'\d+m')
    hour_regex = re.compile(r'\d+h')
    day_regex = re.compile(r'\d+d')

    second = second_regex.findall(value)
    seconds = int(second[0][:-1]) if second else 0

    minute = minute_regex.findall(value)
    minutes = int(minute[0][:-1]) if minute else 0

    hour = hour_regex.findall(value)
    hours = int(hour[0][:-1]) if hour else 0

    day = day_regex.findall(value)
    days = int(day[0][:-1]) if day else 0

    return seconds + minutes * 60 + hours * 3600 + days * 86400
