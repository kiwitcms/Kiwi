# -*- coding: utf-8 -*-

from django.conf.urls import url
from tcms.xmlrpc.views import XMLRPCHandlerFactory


urlpatterns = [
    url(r'^$', XMLRPCHandlerFactory('TCMS_XML_RPC')),
]
