# -*- coding: utf-8 -*-
import datetime

try:
    # Nitrate may not be running under MySQL
    from MySQLdb.constants import FIELD_TYPE
    from django.db.backends.mysql.base import django_conversions
    django_conversions.update({FIELD_TYPE.TIME: None})
except ImportError:
    pass

from django.conf import settings
from django.db.models.fields import IntegerField
from django.db import models

from tcms.core.forms.fields import DurationField as DurationFormField


class BlobValueWrapper(object):
    """
    Wrap the blob value so that we can override the unicode method.
    After the query succeeds, Django attempts to record the last query
    executed, and at that point it attempts to force the query string
    to unicode. This does not work for binary data and generates an
    uncaught exception.
    """

    def __init__(self, val):
        self.val = val

    def __str__(self):
        return self.val

    def __unicode__(self):
        return u'blobdata_unicode'


class BlobField(models.Field):
    """A field for persisting binary data in databases that we support."""
    __metaclass__ = models.SubfieldBase

    def db_type(self, connection):
        engine = connection.settings_dict['ENGINE']
        if engine == 'django.db.backends.mysql':
            return 'LONGBLOB'
        elif engine == 'django.db.backends.postgresql_psycopg2':
            return 'bytea'
        elif engine == 'django.db.backends.sqlite3':
            return 'bytea'
        else:
            raise NotImplementedError

    def to_python(self, value):
        if settings.DATABASE_ENGINE == 'postgresql_psycopg2':
            if value is None:
                return value
            return str(value)
        else:
            return value

    def get_db_prep_save(self, value, connection):
        if value is None:
            return None
        if settings.DATABASE_ENGINE == 'postgresql_psycopg2':
            try:
                import psycopg2
            except ImportError:
                raise

            return psycopg2.Binary(value)
        else:
            return str(value)


class DurationField(IntegerField):
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if isinstance(value, (int, long)):
            return datetime.timedelta(seconds=value)
        elif isinstance(value, datetime.timedelta):
            return value
        else:
            raise TypeError('Unable to convert %s to timedelta.' % value)

    def get_db_prep_value(self, value, connection, prepared):
        """convert datetime.timedelta to seconds.

        1 day equal to 86400 seconds
        """
        if isinstance(value, datetime.timedelta):
            return value.seconds + (86400 * value.days)
        else:
            value = super(DurationField, self).get_db_prep_value(value,
                                                                 connection,
                                                                 prepared)
            return value

    def formfield(self, form_class=DurationFormField, **kwargs):
        defaults = {'help_text': 'Enter duration in the format: DDHHMM'}
        defaults.update(kwargs)
        return form_class(**defaults)
