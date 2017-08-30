# -*- coding: utf-8 -*-

import datetime
import random

from hashlib import sha1

from django.db import models


class UserActivateKey(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    activation_key = models.CharField(max_length=40, null=True, blank=True)
    key_expires = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = u'tcms_user_activate_keys'

    @classmethod
    def set_random_key_for_user(cls, user, force=False):
        salt = sha1(str(random.random()).encode('utf-8')).hexdigest()[:5]
        activation_key = sha1((salt + user.username).encode('utf-8')).hexdigest()

        # Create and save their profile
        k, c = cls.objects.get_or_create(user=user)
        if c or force:
            k.activation_key = activation_key
            k.key_expires = datetime.datetime.today() + datetime.timedelta(7)
            k.save()

        return k
