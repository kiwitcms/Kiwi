# -*- coding: utf-8 -*-
def obj2dict(obj):
    memberlist = [m for m in dir(obj)]
    _dict = {}
    for m in memberlist:
        if m[0] != "_" and not callable(m):
            _dict[m] = getattr(obj, m)

    return _dict
