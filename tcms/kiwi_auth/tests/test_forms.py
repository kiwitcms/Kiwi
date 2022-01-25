import importlib

from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _

from tcms.kiwi_auth import forms


class TestCaptchaField(TestCase):
    def setUp(self):
        self.data = {
            "username": "test_user",
            "password1": "password",
            "password2": "password",
            "email": "new-tester@example.com",
        }

    def test_captcha_required_when_enabled(self):
        importlib.reload(forms)
        form = forms.RegistrationForm(data=self.data)

        self.assertFalse(form.is_valid())
        self.assertIn("captcha", form.errors.keys())
        self.assertIn(_("This field is required."), form.errors["captcha"])

    def test_captcha_fails_when_wrong(self):
        data = self.data.copy()
        data["captcha_0"] = "correct"
        data["captcha_1"] = "WRONG"

        importlib.reload(forms)
        form = forms.RegistrationForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("captcha", form.errors.keys())
        self.assertIn(_("Invalid CAPTCHA"), form.errors["captcha"])

    @override_settings(USE_CAPTCHA=False)
    def test_captcha_not_required_when_disabled(self):
        importlib.reload(forms)
        form = forms.RegistrationForm(data=self.data)

        self.assertTrue(form.is_valid())
        self.assertNotIn("captcha", form.errors.keys())


@override_settings(USE_CAPTCHA=False)
class TestRegistrationForm(TestCase):
    def setUp(self):
        self.data = {
            "username": "test_user",
            "password1": "password",
            "password2": "password",
            "email": "new-tester@example.com",
        }

    def test_user_not_created_when_commit(self):
        importlib.reload(forms)
        form = forms.RegistrationForm(data=self.data)

        user = form.save(commit=False)
        self.assertIsNone(user.pk)

    def test_user_created_when_commit(self):
        importlib.reload(forms)
        form = forms.RegistrationForm(data=self.data)

        user = form.save()
        self.assertIsNotNone(user.pk)
