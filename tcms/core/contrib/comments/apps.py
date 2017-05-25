# -*- coding: utf-8 -*-

from django.apps import AppConfig as DjangoAppConfig
from django.utils.translation import ugettext_lazy as _


class AppConfig(DjangoAppConfig):
    name = 'tcms.core.contrib.comments'
    label = 'kiwi_comments'
    verbose_name = _("Core customized comments")
