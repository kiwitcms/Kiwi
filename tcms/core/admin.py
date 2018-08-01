# -*- coding: utf-8 -*-

from django.urls import reverse
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.contrib.sites.models import Site
from django.contrib.sites.admin import SiteAdmin

from django_comments.models import Comment


class KiwiSiteAdmin(SiteAdmin):
    """
        Does not allow adding new or deleting sites.
        Redirects to the edit form for the default object!
    """
    def add_view(self, request, form_url='', extra_context=None):
        return HttpResponseRedirect(reverse('admin:sites_site_change', args=[settings.SITE_ID]))

    def delete_view(self, request, object_id, extra_context=None):
        return HttpResponseRedirect(reverse('admin:sites_site_change', args=[settings.SITE_ID]))


# we don't want comments to be accessible via the admin interface
admin.site.unregister(Comment)
# site admin with limited functionality
admin.site.unregister(Site)
admin.site.register(Site, KiwiSiteAdmin)

# globally disable the 'Delete selected' action
# see https://github.com/kiwitcms/Kiwi/issues/221 and
# https://docs.djangoproject.com/en/2.0/ref/contrib/admin/actions/#disabling-actions
admin.site.disable_action('delete_selected')
