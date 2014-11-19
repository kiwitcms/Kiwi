# -*- coding: utf-8 -*-
from django.contrib import admin

from kobo.django.xmlrpc.models import XmlRpcLog


class NitrateXmlRpcLogAdmin(admin.ModelAdmin):
    list_display = ('happened_on', 'user_username', 'method')
    list_per_page = 50
    list_filter = ('dt_inserted',)

    user_cache = {}

    def __init__(self, *args, **kwargs):
        NitrateXmlRpcLogAdmin.user_cache.clear()
        NitrateXmlRpcLogAdmin.user_cache = {}

        super(NitrateXmlRpcLogAdmin, self).__init__(*args, **kwargs)

    def user_username(self, obj):
        username = NitrateXmlRpcLogAdmin.user_cache.get(obj.user_id)
        if username is None:
            username = obj.user.username
            NitrateXmlRpcLogAdmin.user_cache[obj.user_id] = username
        return username

    user_username.short_description = 'username'

    def happened_on(self, obj):
        return obj.dt_inserted

    happened_on.short_description = 'Happened On'


admin.site.unregister(XmlRpcLog)
admin.site.register(XmlRpcLog, NitrateXmlRpcLogAdmin)
