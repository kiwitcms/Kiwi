# -*- coding: utf-8 -*-

from django import forms
from django.urls import reverse
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.contrib.auth.models import Permission, User
from django.contrib.sites.models import Site
from django.contrib.auth.admin import UserAdmin
from django.contrib.sites.admin import SiteAdmin
from django.contrib.auth.forms import UserChangeForm
from django.utils.translation import ugettext_lazy as _

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


class UniqueEmailForm:
    """
        Enforces unique user emails.
    """
    def clean_email(self):
        qs = User.objects.filter(email=self.cleaned_data['email'])
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.count():
            raise forms.ValidationError(_('This email address is already in use'))
        else:
            return self.cleaned_data['email']


class MyUserChangeForm(UniqueEmailForm, UserChangeForm):
    email = forms.EmailField(required=True)


class KiwiUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('is_superuser', 'date_joined', 'last_login')
    ordering = ['-pk']  # same as -date_joined

    # override standard form and make the email address unique
    # even when adding users via admin panel
    form = MyUserChangeForm

    def change_view(self, request, object_id, extra_context=None):
        if request.user.is_superuser:
            return super().change_view(request, object_id, extra_context)

        # object history view link to admin_user_change so we redirect
        # to the user profile instead
        user = User.objects.get(pk=object_id)
        return HttpResponseRedirect(reverse('tcms-profile', args=[user.username]))

    def _modifying_myself(self, request, object_id):
        return request.user.pk == int(object_id)

    @admin.options.csrf_protect_m
    def delete_view(self, request, object_id, extra_context=None):
        # if trying to delete another user go directly to parent
        if not self._modifying_myself(request, object_id):
            return super().delete_view(request, object_id, extra_context)

        # else allow deletion of the user own account
        permission = Permission.objects.get(content_type__app_label='auth',
                                            codename='delete_user')
        try:
            request.user.user_permissions.add(permission)
            return super().delete_view(request, object_id, extra_context)
        finally:
            request.user.user_permissions.remove(permission)

    def response_delete(self, request, obj_display, obj_id):
        result = super().response_delete(request, obj_display, obj_id)

        if not self._modifying_myself(request, obj_id):
            return result

        # user doesn't exist anymore so go to the index page
        # instead of returning to the user admin page
        return HttpResponseRedirect(reverse('core-views-index'))

    def has_delete_permission(self, request, obj=None):
        # allow to delete yourself without having 'delete' permission
        # explicitly assigned
        if self._modifying_myself(request, getattr(obj, 'pk', 0)):
            return True

        return super().has_delete_permission(request, obj)


# we don't want comments to be accessible via the admin interface
admin.site.unregister(Comment)
# site admin with limited functionality
admin.site.unregister(Site)
admin.site.register(Site, KiwiSiteAdmin)

# user admin extended functionality
admin.site.unregister(User)
admin.site.register(User, KiwiUserAdmin)

# globally disable the 'Delete selected' action
# see https://github.com/kiwitcms/Kiwi/issues/221 and
# https://docs.djangoproject.com/en/2.0/ref/contrib/admin/actions/#disabling-actions
admin.site.disable_action('delete_selected')
