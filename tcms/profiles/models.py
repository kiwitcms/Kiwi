# -*- coding: utf-8 -*-
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField('auth.User', unique=True, related_name='profile',
                                on_delete=models.CASCADE)
    phone_number = models.CharField(blank=True, default='', max_length=128)
    url = models.URLField(blank=True, default='')
    im = models.CharField(blank=True, default='', max_length=128)
    im_type_id = models.IntegerField(blank=True, default=1, null=True)
    address = models.TextField(blank=True, default='')
    notes = models.TextField(blank=True, default='')

    def get_im(self):
        # to avoid circular imports
        from .forms import IM_CHOICES

        if not self.im:
            return None

        for choice in IM_CHOICES:
            if self.im_type_id == choice[0]:
                return '[%s] %s' % (choice[1], self.im)

        raise ValueError('Invalid IM type id')

    @classmethod
    def get_user_profile(cls, user):
        return cls.objects.get(user=user)
