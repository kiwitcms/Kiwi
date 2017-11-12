# -*- coding: utf-8 -*-

from __future__ import absolute_import
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^environment/groups/$', views.environment_groups,
        name='management-env-groups'),
    url(r'^environment/group/edit/$', views.environment_group_edit,
        name='management-env-group-edit'),
    url(r'^environment/properties/$', views.environment_properties,
        name='management-env-properties'),
    url(r'^environment/properties/values/$', views.environment_property_values,
        name='management-env-properties-values'),
]
