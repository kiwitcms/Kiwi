# -*- coding: utf-8 -*-

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin, UserAdmin, sensitive_post_parameters_m
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from tcms.utils.user import delete_user

User = get_user_model()  # pylint: disable=invalid-name


class MyUserChangeForm(UserChangeForm):
    """
    Enforces unique user emails.
    """

    email = forms.EmailField(required=True)

    def clean_email(self):
        query_set = User.objects.filter(email=self.cleaned_data["email"])
        if self.instance:
            query_set = query_set.exclude(pk=self.instance.pk)
        if query_set.count():
            raise forms.ValidationError(_("This email address is already in use"))

        return self.cleaned_data["email"]


def _modifying_myself(request, object_id):
    return request.user.pk == int(object_id)


class GroupAdminForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name", "permissions"]

    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("users", False),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["users"].label = capfirst(_("users"))
        if self.instance.pk:
            self.fields["users"].initial = self.instance.user_set.all()

    def save(self, commit=True):
        instance = super().save(commit=commit)
        instance.save()

        self.instance.user_set.set(self.cleaned_data["users"])
        self.save_m2m()

        return instance


class KiwiUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + (
        "is_active",
        "is_superuser",
        "date_joined",
        "last_login",
    )
    ordering = ["-pk"]  # same as -date_joined

    # override standard form and make the email address unique
    # even when adding users via admin panel
    form = MyUserChangeForm

    def has_view_permission(self, request, obj=None):
        return _modifying_myself(
            request, getattr(obj, "pk", 0)
        ) or super().has_view_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        return _modifying_myself(
            request, getattr(obj, "pk", 0)
        ) or super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return _modifying_myself(
            request, getattr(obj, "pk", 0)
        ) or super().has_delete_permission(request, obj)

    # pylint: disable=too-many-arguments
    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        if not self.has_change_permission(request, obj):
            context.update(
                {
                    "show_save": False,
                    "show_save_and_continue": False,
                }
            )
        context.update(
            {
                "show_save_and_add_another": self.has_add_permission(request),
            }
        )
        return super().render_change_form(
            request, context, add=add, change=change, form_url=form_url, obj=obj
        )

    def get_readonly_fields(self, request, obj=None):
        # adding new user
        if not obj:
            return super().get_readonly_fields(request, obj)

        readonly_fields = [
            "username",
            "last_login",
            "date_joined",
        ]

        # only other superusers can set the is_superuser flag
        if not request.user.is_superuser:
            readonly_fields.append("is_superuser")

        # if you have explicit change_user permission you can modify these fields
        # however users are not able to give themselves elevated permissions
        if not self.has_change_permission(request, None):
            readonly_fields.extend(
                [
                    "is_staff",
                    "is_active",
                    "groups",
                    "user_permissions",
                ]
            )

            # lastly users can't modify others unless they have the expolicit permission
            if not _modifying_myself(request, obj.pk):
                readonly_fields.extend(["first_name", "last_name", "email"])

        return readonly_fields

    def get_fieldsets(self, request, obj=None):
        # adding new account b/c we have permissions
        if not obj and self.has_add_permission(request):
            return super().get_fieldsets(request, obj)

        first_fieldset_fields = ("username",)
        if obj and _modifying_myself(request, obj.pk):
            first_fieldset_fields += ("password",)

        remaining_fieldsets = (
            (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
            (
                _("Permissions"),
                {
                    "fields": (
                        "is_active",
                        "is_staff",
                        "is_superuser",
                        "groups",
                        "user_permissions",
                    )
                },
            ),
        )

        if request.user.is_superuser:
            field_sets = super().get_fieldsets(request, obj)
            if field_sets[0][0] is None and "password" in field_sets[0][1]["fields"]:
                remaining_fieldsets = field_sets[1:]

        return ((None, {"fields": first_fieldset_fields}),) + remaining_fieldsets

    @sensitive_post_parameters_m
    def user_change_password(
        self, request, id, form_url=""
    ):  # pylint: disable=redefined-builtin
        if _modifying_myself(request, id):
            return HttpResponseRedirect(reverse("admin:password_change"))

        raise PermissionDenied

    @admin.options.csrf_protect_m
    def delete_view(self, request, object_id, extra_context=None):
        if not _modifying_myself(request, object_id):
            return super().delete_view(request, object_id, extra_context)

        # allow deletion of the user own account
        permission = Permission.objects.get(
            content_type__app_label="auth", codename="delete_user"
        )
        try:
            request.user.user_permissions.add(permission)
            return super().delete_view(request, object_id, extra_context)
        finally:
            request.user.user_permissions.remove(permission)

    def response_delete(self, request, obj_display, obj_id):
        result = super().response_delete(request, obj_display, obj_id)

        if not _modifying_myself(request, obj_id):
            return result

        # user doesn't exist anymore so go to the login page
        return HttpResponseRedirect(reverse("tcms-login"))

    def delete_model(self, request, obj):
        delete_user(obj)


class KiwiGroupAdmin(GroupAdmin):
    form = GroupAdminForm

    def has_delete_permission(self, request, obj=None):
        if obj and obj.name in ["Tester", "Administrator"]:
            return False
        return super().has_delete_permission(request, obj)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj=obj)
        name_index = fields.index("name")

        # make sure Name is always the first field
        if name_index > 0:
            del fields[name_index]
            fields.insert(0, "name")

        return fields

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)

        if obj and obj.name in ["Tester", "Administrator"]:
            readonly_fields += ("name",)

        return readonly_fields


# user admin extended functionality
admin.site.unregister(User)
admin.site.register(User, KiwiUserAdmin)
admin.site.unregister(Group)
admin.site.register(Group, KiwiGroupAdmin)
