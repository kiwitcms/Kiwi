# -*- coding: utf-8 -*-

from django import forms
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from tcms.core.utils import string_to_list


class UserField(forms.CharField):
    """
    Custom field type.
    Will eventually support user selection
    """

    def clean(self, value):
        """
        Form-validation:  accept a string/integer.
        Looks at both email address and real name.
        """
        if value == '' or value is None:
            if self.required:
                raise ValidationError('A user name or user ID is required.')
            else:
                return None
        if isinstance(value, int):
            try:
                return User.objects.get(pk=value)
            except User.DoesNotExist:
                raise ValidationError('Unknown user_id: "%s"' % value)
        else:
            value = value.strip()
            if value.isdigit():
                try:
                    return User.objects.get(pk=value)
                except User.DoesNotExist:
                    raise ValidationError('Unknown user_id: "%s"' % value)
            else:
                try:
                    return User.objects.get(
                        (Q(email=value) | Q(username=value)))
                except User.DoesNotExist:
                    raise ValidationError('Unknown user: "%s"' % value)


class MultipleEmailField(forms.EmailField):
    def clean(self, value):
        """
        Validates that the input matches the regular expression. Returns a
        Unicode object.
        """
        value = super(forms.CharField, self).clean(value)
        if value == u'':
            return value

        return [v for v in string_to_list(strs=value) if self.regex.search(v)]


class StripURLField(forms.URLField):
    def to_python(self, value):
        if isinstance(value, str):
            value = value.strip()
        return super(StripURLField, self).to_python(value)


class ModelChoiceField(forms.ModelChoiceField):
    def to_python(self, value):
        try:
            return super(ModelChoiceField, self).to_python(value)
        except ValidationError as e:
            raise ValidationError(e.messages[0] % {'value': value})
