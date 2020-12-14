# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q

User = get_user_model()  # pylint: disable=invalid-name


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
        if value == "" or value is None:
            if self.required:
                raise ValidationError("A user name or user ID is required.")
            return None
        if isinstance(value, int):
            try:
                return User.objects.get(pk=value)
            except User.DoesNotExist:
                raise ValidationError('Unknown user_id: "%s"' % value) from None
        else:
            value = value.strip()
            if value.isdigit():
                try:
                    return User.objects.get(pk=value)
                except User.DoesNotExist:
                    raise ValidationError('Unknown user_id: "%s"' % value) from None
            else:
                try:
                    return User.objects.get((Q(email=value) | Q(username=value)))
                except User.DoesNotExist:
                    raise ValidationError('Unknown user: "%s"' % value) from None
