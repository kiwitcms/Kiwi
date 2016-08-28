# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import get_backends

from models import UserProfile
from tcms.core.forms import StripURLField


IM_CHOICES = (
    (1, 'IRC'),
    (2, 'Jabber'),
    (3, 'MSN'),
    (4, 'Yahoo messenger'),
    (5, 'ICQ')
)

BOOKMARK_EMPTY_LABEL = '---all---'


class UserProfileForm(forms.ModelForm):
    user = forms.CharField(widget=forms.HiddenInput)
    username = forms.RegexField(
        label=_("Username"), max_length=30, regex=r'^[\w.@+-]+$',
        help_text=_(
            "Required. 30 characters or fewer. "
            "Letters, digits and @/./+/-/_ only."),
        error_messages={'invalid': _(
            "This value may contain only letters, "
            "numbers and @/./+/-/_ characters.")},
    )
    first_name = forms.CharField(max_length=128, required=False)
    last_name = forms.CharField(max_length=128, required=False)
    email = forms.EmailField(label=_("E-mail"), max_length=75)
    im_type_id = forms.ChoiceField(choices=IM_CHOICES)
    url = StripURLField(required=False)

    class Meta:
        model = UserProfile
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        if 'url' in kwargs:
            kwargs['url'] = kwargs['url'].strip()
        super(UserProfileForm, self).__init__(*args, **kwargs)
        if 'instance' in kwargs:
            instance = kwargs['instance']
            self.initial['username'] = instance.user.username
            self.initial['first_name'] = instance.user.first_name
            self.initial['last_name'] = instance.user.last_name
            self.initial['email'] = instance.user.email

    def clean_email(self):
        email = self.cleaned_data['email']
        if not getattr(self.instance, 'pk'):
            return email

        if email == self.instance.user.email:
            return email

        try:
            u = User.objects.get(email=email)
        except ObjectDoesNotExist:
            return email

        if u == self.instance:
            return u.email

        raise forms.ValidationError(
            _("A user with that email already exists."))

    def clean_user(self):
        if not self.instance.pk:
            return User.objects.get(pk=self.cleaned_data['user'])

        if self.instance.user.pk == int(self.cleaned_data['user']):
            return self.instance.user

        raise forms.ValidationError(_("User error."))

    def clean_username(self):
        username = self.cleaned_data['username']

        if not getattr(self.instance, 'pk'):
            return username

        if username == self.instance.user.username:
            return username

        try:
            u = User.objects.get(username=username)
        except ObjectDoesNotExist:
            return username

        if u == self.instance:
            return username

        raise forms.ValidationError(
            _("A user with that username already exists."))

    def save(self, commit=True):
        can_register = False

        for b in get_backends():
            if getattr(b, 'can_register', None):
                can_register = True

        instance = super(UserProfileForm, self).save(commit=commit)
        user = instance.user
        if can_register:
            user.username = self.cleaned_data['username']
            user.email = self.cleaned_data['email']

        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        return instance


class BookmarkForm(forms.Form):
    a = forms.CharField(widget=forms.HiddenInput)
    content_type = forms.CharField(
        required=False, widget=forms.HiddenInput
    )
    object_pk = forms.CharField(
        required=False, widget=forms.HiddenInput
    )
    user = forms.IntegerField(widget=forms.HiddenInput)
    url = StripURLField()
    name = forms.CharField(max_length=1024, required=False)
    description = forms.CharField(required=False, widget=forms.Textarea)

    def clean(self):
        from django.conf import settings
        from django.db import models
        from django.core.exceptions import ObjectDoesNotExist, ValidationError
        from django.contrib.sites.models import Site
        from django.contrib.auth.models import User
        from django.contrib.contenttypes.models import ContentType

        cleaned_data = self.cleaned_data.copy()
        if cleaned_data.get('content_type'):
            try:
                m = models.get_model(
                    *cleaned_data['content_type'].split(".", 1))
                target = m._default_manager.get(pk=cleaned_data['object_pk'])
                app_label, model = cleaned_data['content_type'].split(".", 1)
                ct = ContentType.objects.get(
                    app_label=app_label, model=model
                )
                cleaned_data['content_type'] = ct
                cleaned_data['object_pk'] = target.pk
            except ObjectDoesNotExist, error:
                raise ValidationError(error)

        cleaned_data['user'] = User.objects.get(pk=cleaned_data['user'])
        cleaned_data['site'] = Site.objects.get(pk=settings.SITE_ID)
        return cleaned_data

    def populate(self, user):
        pass

    def save(self):
        from models import Bookmark

        cleaned_data = self.cleaned_data.copy()
        del cleaned_data['a']
        if not cleaned_data['content_type']:
            del cleaned_data['content_type']
            del cleaned_data['object_pk']
        return Bookmark.objects.create(**cleaned_data)
