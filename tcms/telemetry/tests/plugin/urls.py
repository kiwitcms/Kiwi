# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^example/$', views.Example.as_view(), name='a_fake_plugin-example_view'),
]
