# -*- coding: utf-8 -*-
import datetime

try:
    # may not be running under MySQL
    from MySQLdb.constants import FIELD_TYPE
    from django.db.backends.mysql.base import django_conversions
    django_conversions.update({FIELD_TYPE.TIME: None})
except ImportError:
    pass

from django.db.models.fields import IntegerField

from tcms.core.forms.fields import DurationField as DurationFormField


class DurationField(IntegerField):
    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        if isinstance(value, int):
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
