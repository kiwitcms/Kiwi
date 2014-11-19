# -*- coding: utf-8 -*-
import hashlib


def checksum(value):
    if value is None:
        return ''
    md5 = hashlib.md5()
    md5.update(value.encode("UTF-8"))
    return md5.hexdigest()
