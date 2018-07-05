# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import get_backends


from tcms.profiles.models import UserProfile
from tcms.core.forms.fields import StripURLField

IM_CHOICES = (
    (1, 'IRC'),
    (2, 'Jabber'),
    (3, 'MSN'),
    (4, 'Yahoo messenger'),
    (5, 'ICQ')
)


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
            user = User.objects.get(email=email)
        except ObjectDoesNotExist:
            return email

        if user == self.instance:
            return user.email

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
            user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            return username

        if user == self.instance:
            return username

        raise forms.ValidationError(
            _("A user with that username already exists."))

    def save(self, commit=True):
        can_register = False

        for backend in get_backends():
            if getattr(backend, 'can_register', None):
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
