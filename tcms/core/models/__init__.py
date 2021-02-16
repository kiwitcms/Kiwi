# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model

get_user_model()._meta.ordering = ["username"]
