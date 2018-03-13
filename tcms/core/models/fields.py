# -*- coding: utf-8 -*-
try:
    # may not be running under MySQL
    from MySQLdb.constants import FIELD_TYPE
    from django.db.backends.mysql.base import django_conversions
    django_conversions.update({FIELD_TYPE.TIME: None})
except ImportError:
    pass
