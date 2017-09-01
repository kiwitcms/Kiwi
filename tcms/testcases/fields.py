# -*- coding: utf-8 -*-
from itertools import filterfalse

from django.forms import EmailField
from django.forms import ValidationError

__all__ = ['MultipleEmailField', 'CC_LIST_DEFAULT_DELIMITER', ]

CC_LIST_DEFAULT_DELIMITER = ','


class MultipleEmailField(EmailField):
    ''' Holding mulitple email addresses '''

    default_error_messages = {
        'invalid': u'%(value)s is/are not valid email addresse(s).',
    }

    def __init__(self, delimiter=CC_LIST_DEFAULT_DELIMITER, *args, **kwargs):

        super(MultipleEmailField, self).__init__(*args, **kwargs)
        self.delimiter = delimiter

    def to_python(self, value):

        if not value:
            return []

        if not isinstance(value, str):
            raise ValidationError(
                '%s is not a valid string value.' % str(value))

        result = [item.strip() for item in filterfalse(
            lambda item: item.strip() == '', value.split(self.delimiter))]
        return result

    def clean(self, value):
        email_addrs = self.to_python(value)
        super_instance = super(MultipleEmailField, self)

        valid_email_addrs = []
        invalid_email_addrs = []

        self.validate(email_addrs)

        for email_addr in email_addrs:
            try:
                super_instance.run_validators(email_addr)
            except ValidationError:
                invalid_email_addrs.append(email_addr)
            else:
                valid_email_addrs.append(email_addr)

        if invalid_email_addrs:
            raise ValidationError(
                self.error_messages['invalid'] % {
                    'value': ', '.join(invalid_email_addrs)})

        return valid_email_addrs
