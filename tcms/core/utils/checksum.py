# -*- coding: utf-8 -*-
import hashlib


def checksum(value):
    if value is None:
        return ''
    _checksum = hashlib.sha256()
    _checksum.update(value.encode("UTF-8"))
    return _checksum.hexdigest()
