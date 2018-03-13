# -*- coding: utf-8 -*-
import datetime


def format_timedelta(timedelta):
    '''convert instance of datetime.timedelta to d(ay), h(our), m(inute)'''
    if isinstance(timedelta, datetime.timedelta):
        m, s = divmod(timedelta.seconds, 60)
        h, m = divmod(m, 60)
        d = timedelta.days
        day = '%dd' % d if d else ''
        hour = '%dh' % h if h else ''
        minute = '%dm' % m if m else ''
        second = '%ds' % s if s else ''
        timedelta_str = day + hour + minute + second
        return timedelta_str if timedelta_str else '0'
    else:
        raise TypeError(
            'Unable to convert %s to d(ay):h(our):m(inute):s(econd)'
            % timedelta)
