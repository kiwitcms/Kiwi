# -*- coding: utf-8 -*-
import datetime
import six

from pymysql.constants import FIELD_TYPE
from django.db.models.fields import IntegerField
from django.db.backends.mysql.base import django_conversions

from tcms.core.forms.fields import DurationField as DurationFormField

django_conversions.update({FIELD_TYPE.TIME: None})


class DurationField(IntegerField):
    """Duration field for test run

    Value is stored as number of seconds in database and presents in Nitrate in
    timedelta type.

    Value should also be able to be serialized to integer as seconds, and then
    deserialized from value of seconds.
    """

    def to_python(self, value):
        if isinstance(value, six.integer_types):
            return datetime.timedelta(seconds=value)
        elif isinstance(value, datetime.timedelta):
            return value
        else:
            raise TypeError('Unable to convert %s to timedelta.' % value)

    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return value
        return datetime.timedelta(seconds=value)

    def get_db_prep_value(self, value, connection, prepared=True):
        """convert datetime.timedelta to seconds.

        1 day equal to 86400 seconds
        """
        if isinstance(value, datetime.timedelta):
            return value.seconds + (86400 * value.days)
        else:
            value = super(DurationField, self).get_db_prep_value(
                value, connection, prepared)
            return value

    def formfield(self, form_class=DurationFormField, **kwargs):
        defaults = {'help_text': 'Enter duration in the format: DDHHMM'}
        defaults.update(kwargs)
        return form_class(**defaults)
